--!native
--!optimize 2
local EncodingService = game:GetService("EncodingService")
local RunService = game:GetService("RunService")

local WavPlayer = {}

function WavPlayer.Play(targetPart, wavDataFolder)
	if not targetPart or not wavDataFolder then return end

	local totalChunks = tonumber(wavDataFolder:WaitForChild("TotalChunks", 5).Value)
	local chunks = {}
	for i = 1, totalChunks do
		local chunkVal = wavDataFolder:WaitForChild(tostring(i), 5)
		if chunkVal then chunks[i] = chunkVal.Value else return end
	end

	local b64_data = table.concat(chunks)
	local decoded_buf = EncodingService:Base64Decode(buffer.fromstring(b64_data))
	local data = decoded_buf

	local windowSize = 512
	local baseComponentFrequency = 440
	local playbackSpeed = 1
	local volume = 1
	local bitCrush = 1
	local pitchAmount = 1
	local distAmount = 0
	local timePosition = 0
	local playing = false
	local looping = true

	local byteOffset = 16
	local formatChunkSize, channels, samplingRate, bitsPerSample
	local header, dataSize, samples, maxValue

	local waves = {}
	local function makeSine(i, frequency)
		local s = Instance.new("Sound")
		s.SoundId = "rbxassetid://9040512197"
		s.Volume = 0
		s.Playing = true
		s.Looped = true
		s.Parent = targetPart
		s.Name = i
		s.RollOffMaxDistance = 100

		local freqPbs = frequency / baseComponentFrequency
		if freqPbs > 20 then
			freqPbs = frequency / 1050
			s.SoundId = "rbxassetid://198099744"
		end
		s.PlaybackSpeed = freqPbs
		return s
	end

	for i = 0, windowSize / 2 do
		table.insert(waves, makeSine(i, 0))
	end

	local function getString(length, offset, blob)
		local str = ""
		for i = 0, length - 1 do
			str = str..string.char(buffer.readu8(blob, offset + i))
		end
		return str
	end

	local function createFftState(size)
		local state = {}
		local log2n = math.log(size) / math.log(2)
		state.bitRev = {}
		for i = 0, size - 1 do
			local rev = 0
			local temp = i
			for j = 0, log2n - 1 do
				rev = bit32.bor(bit32.lshift(rev, 1), bit32.band(temp, 1))
				temp = bit32.rshift(temp, 1)
			end
			state.bitRev[i] = rev
		end
		state.cosTable = {}
		state.sinTable = {}
		for k = 0, size // 2 - 1 do
			local angle = -2 * math.pi * k / size
			state.cosTable[k] = math.cos(angle)
			state.sinTable[k] = math.sin(angle)
		end
		return state
	end

	local function fft(reals, imaginaries, state)
		local n = #reals
		local bitRev = state.bitRev
		local cosTable = state.cosTable
		local sinTable = state.sinTable
		for i = 0, n - 1 do
			local j = bitRev[i]
			if j > i then
				reals[i + 1], reals[j + 1] = reals[j + 1], reals[i + 1]
				imaginaries[i + 1], imaginaries[j + 1] = imaginaries[j + 1], imaginaries[i + 1]
			end
		end
		local m = 1
		while m < n do
			local m2 = m * 2
			for k = 0, m - 1 do
				local cos = cosTable[k * n // m2]
				local sin = sinTable[k * n // m2]
				for j = k, n - 1, m2 do
					local t_re = cos * reals[j + m + 1] - sin * imaginaries[j + m + 1]
					local t_im = sin * reals[j + m + 1] + cos * imaginaries[j + m + 1]
					reals[j + m + 1] = reals[j + 1] - t_re
					imaginaries[j + m + 1] = imaginaries[j + 1] - t_im
					reals[j + 1] = reals[j + 1] + t_re
					imaginaries[j + 1] = imaginaries[j + 1] + t_im
				end
			end
			m = m2
		end
		return reals, imaginaries
	end

	local state = createFftState(windowSize)

	byteOffset = 16
	formatChunkSize = buffer.readu32(data, byteOffset)
	byteOffset = 22
	channels = buffer.readu16(data, byteOffset)
	byteOffset = 24
	samplingRate = buffer.readu32(data, byteOffset)
	byteOffset = 34
	bitsPerSample = buffer.readu16(data, byteOffset)
	byteOffset = byteOffset + 2

	if formatChunkSize == 18 then
		byteOffset = byteOffset + 2
	elseif formatChunkSize == 40 then
		byteOffset = byteOffset + 24
	elseif formatChunkSize ~= 16 then
		error("Invalid wav file")
	elseif channels == 2 then
		error("File must be mono")
	end

	header = ""
	while header ~= "data" do
		header = getString(4, byteOffset, data)
		byteOffset = byteOffset + 1
	end
	byteOffset = byteOffset + 3
	dataSize = buffer.readu32(data, byteOffset)
	samples = dataSize / channels / (bitsPerSample / 8)
	maxValue = 2 ^ bitsPerSample

	for i, wave in next, waves do
		i = i - 1
		local frequency = i * samplingRate / windowSize * math.abs(playbackSpeed)
		local freqPbs = frequency / baseComponentFrequency
		if freqPbs > 20 then
			freqPbs = frequency / 1050
			wave.SoundId = "rbxassetid://198099744"
		else
			wave.SoundId = "rbxassetid://9040512197"
		end
		wave.PlaybackSpeed = freqPbs
		wave.Parent = targetPart
	end
	playing = true

	local deltaTime = 0
	local previousWaitTime = os.clock()
	local previousIndex = -1
	local reals = {}
	local imaginaries = {}
	local conn
	local stopped = false

	local function play()
		if stopped then return end
		if not wavDataFolder or not wavDataFolder.Parent or not targetPart or not targetPart.Parent then
			stopped = true
			playing = false
			for i, wave in next, waves do
				wave.Volume = 0
				if wave.Playing then wave:Stop() end
				pcall(function() wave:Destroy() end)
			end
			if conn then conn:Disconnect() end
			return
		end

		if playing and targetPart:IsDescendantOf(game) then
			timePosition = (timePosition + deltaTime * playbackSpeed)
			if looping then
				timePosition %= (samples / samplingRate)
			else
				if timePosition >= (samples / samplingRate) then
					playing = false
					for i, wave in next, waves do
						wave.Volume = 0
						if wave.Playing then wave:Stop() end	
					end
					return
				end
			end

			local index = math.floor(timePosition * (samplingRate / windowSize)) * windowSize
			if index > (samples - windowSize) then index = samples - windowSize
			elseif index < 0 then index = 0 end

			if index ~= previousIndex then
				local previousSample = 0
				for i = 1, windowSize do
					local sample = 0
					if bitsPerSample == 8 then
						sample = buffer.readi8(data, byteOffset + index + (i - 1))
					elseif bitsPerSample == 16 then
						sample = buffer.readi16(data, byteOffset + index * 2 + (i - 1) * 2)
					elseif bitsPerSample == 32 then
						sample = buffer.readi32(data, byteOffset + index * 4 + (i - 1) * 4)
					end

					if i % (bitCrush or 1) == 0 or i == 1 then
						reals[i] = sample / maxValue
					else
						reals[i] = previousSample
					end
					previousSample = reals[i]
					imaginaries[i] = 0
				end

				reals, imaginaries = fft(reals, imaginaries, state)

				for i, wave in pairs(waves) do
					local real = reals[i]
					local imaginary = imaginaries[i]
					local magnitude = Vector2.new(real, imaginary).Magnitude
					local phase = math.atan2(imaginary, real)

					local pit = ((i - 1) * (samplingRate / windowSize)) * math.abs(playbackSpeed)
					local crossPoint = (pit / baseComponentFrequency > 20) and 2.531 or 0.812
					local halfWavePeriod = (pit / baseComponentFrequency > 20) and (1 / 1050 / 2) or (1 / baseComponentFrequency / 2)

					wave.TimePosition = crossPoint + (phase / math.pi) * halfWavePeriod
					wave.Volume = magnitude * 0.01 * volume
					if not wave.Playing then wave:Play() end
				end
			end
			previousIndex = index
		else
			for i, wave in next, waves do
				wave.Volume = 0
				if wave.Playing then wave:Stop() end
			end
		end

		deltaTime = os.clock() - previousWaitTime
		previousWaitTime = os.clock()
	end

	conn = RunService.PreRender:Connect(play)
end

return WavPlayer