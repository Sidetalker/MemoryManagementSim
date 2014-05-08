# Memory Management Simulation System
# Kevin Sullivan
# Gaby Ciavardoni

import sys

MEM_SIZE = 1600
OS_SIZE = 80


# Represents a single process
class Process():
	def __init__(self, name, size, starts, stops):
		self.name = name
		self.size = size
		self.starts = starts	# All process start times
		self.stops = stops		# All process end times
		self.running = False
		self.runCycle = 0

	# Print a human readable description (used for debugging)
	def pprint(self):
		print('%s\t%d\n  %s\n  %s' % (self.name, self.size, self.starts, self.stops))

	# Returns true if the process is starting at the specified time
	def starting(self, time):
		# Flip the running flag and return true if this process is starting
		if self.starts[self.runCycle] == time:
			self.running = True
			return True

		return False

	def ending(self, time):
		# If the process isn't running, it's not ending
		if not self.running:
			return False

		# If the process is ending toggle the run flag and increment the run cycle
		if self.stops[self.runCycle] == time:
			self.running = False
			self.runCycle += 1
			return True


# Represents all available and allocated memory
class Memory():
	def __init__(self, algorithm):
		self.cells = ['#' if x < OS_SIZE else '.' for x in range(MEM_SIZE)]
		self.procs = []
		self.algorithm = algorithm
		self.lastBlock = 0

	# Display memory to spec
	def pprint(self, time):
		print('Memory at time %d:' % time)
		for i in range(0, MEM_SIZE, OS_SIZE):
			print(''.join(self.cells[i:i+OS_SIZE]))
		print()

	# Load one of the processes existing at t=0
	def loadInit(self, proc):
		count = 0
		counting = False

		start = self.cells.index('.')

		for i in range(proc.size):
			location = i + start

			if location >= MEM_SIZE:
				return False

			self.cells[location] = proc.name

		self.lastBlock = start + proc.size - 1
		self.procs.append(proc)

		return True

	# Load a process based on the current algorithm
	def loadProc(self, proc):
		# List of available spaces
		spaces = []
		inFree = False
		startIndex = 0
		freeCount = 0

		# Gather a list of all available spaces (start loc and size)
		for x in range(OS_SIZE, MEM_SIZE):
			if self.cells[x] == '.' and not inFree:
				inFree = True
				startIndex = x
				freeCount = 0
			if self.cells[x] == '.' and inFree:
				freeCount += 1
			if self.cells[x] != '.' and inFree:
				spaces.append((startIndex, freeCount))
				inFree = False

		if inFree:
			spaces.append((startIndex, freeCount))

		# Defrag if we can't find a single available space
		if len(spaces) == 0:
			return False

		chosenSpace = None

		# Find the first space that the process will fit
		if self.algorithm == 'first':
			for space in spaces:
				if space[1] >= proc.size:
					chosenSpace = space
					break

		# Find the smallest space that the process will fit
		elif self.algorithm == 'best':
			for space in spaces:
				if chosenSpace is not None:
					if space[1] >= proc.size and space[1] < chosenSpace[1]:
						chosenSpace = space
				else:
					if space[1] >= proc.size:
						chosenSpace = space

		# Find the next space that the process will fit
		elif self.algorithm == 'next':
			print('spaces: %s' % str(spaces))

			# First search spaces with a start location above the last block
			for space in spaces:
				print('lastblock: %d' % self.lastBlock)
				if space[0] in range(self.lastBlock, 1600) and space[1] >= proc.size:
					chosenSpace = space
					break

			# If we still haven't found a suitable location, check from the beginning
			if chosenSpace is None:
				for space in spaces:
					if space[0] in range(OS_SIZE, self.lastBlock) and space[1] >= proc.size:
						chosenSpace = space
						break

			print('chosenspace: %s' % str(chosenSpace))

		# Find the worst (largest) space that the process will fit
		elif self.algorithm == 'worst':
			for space in spaces:
				if chosenSpace is not None:
					if space[1] >= proc.size and space[1] > chosenSpace[1]:
						chosenSpace = space
				else:
					if space[1] >= proc.size:
						chosenSpace = space

		# Non contiguous memory specified
		elif self.algorithm == 'noncontig':
			# If the process is larger than the available memory - we have failed
			if proc.size > self.cells.count('.'):
				return False

			# Otherwise, loop on through the memory allocating space for the new process
			totalSize = proc.size

			for x in range(OS_SIZE, MEM_SIZE):
				if totalSize == 0:
					break
				else:
					if self.cells[x] == '.':
						self.cells[x] = proc.name
						totalSize -= 1

		# Defrag if we can't find any possible space
		if chosenSpace is None:
			return False

		# Replace memory in the chosen range
		for x in range(chosenSpace[0], chosenSpace[0] + proc.size):
			self.cells[x] = proc.name

		# Save the last block for next fit algorithm
		self.lastBlock = chosenSpace[0] + chosenSpace[1]

		# Return true on successful process load
		self.procs.append(proc)
		return True

	# Remove a process from memory
	def unloadProc(self, proc):
		self.cells = [x if x != proc.name else '.' for x in self.cells]
		self.procs.remove(proc)

	# Simulate a defrag by cleaning out the memory entirely and placing
	# each process back into memory sequentially
	def defrag(self, proc, simTime):
		# If this is noncontigous memory, fail the defrag right away
		if self.algorithm == 'noncontig':
			return False

		# Print init message
		print('Performing defragmentation...')

		# Reset memory
		self.cells = ['#' if x < OS_SIZE else '.' for x in range(MEM_SIZE)]

		# Tracker var
		curCell = OS_SIZE

		# Loop through all processes and place them in memory sequentially
		for proc in self.procs:
			for x in range(curCell, curCell + proc.size):
				self.cells[x] = proc.name
				curCell = x

		# Print completion message
		print('Defragmentation completed.')
		print('Relocated %d processes to create a free memory block of %d units (%.2f%% of total memory).'
			 % (len(self.procs), self.cells.count('.'), self.cells.count('.') / MEM_SIZE * 100))
		print()
		self.pprint(simTime)

		# Attempt to load the process again
		return self.loadProc(proc)


# Manages simulation time and all (inactive and active) processes
class ProcessManager():
	def __init__(self, algorithm):
		self.algorithm = algorithm
		self.simTime = 0

		self.procCount = 0
		self.procs = []

		self.memory = None

	# Load processes from specified input file
	def loadProcs(self, inFile):
		try:
			with open(inFile, 'r') as procData:
				# Get process count
				self.procCount = int(procData.readline().strip())

				# Loop through the rest of the file gathering process info
				for line in procData.readlines():
					splitLine = line.split()

					# Gather data for the current process
					name = splitLine[0]
					size = int(splitLine[1])
					starts = [int(x) for x in splitLine[2::2]]
					stops = [int(x) for x in splitLine[3::2]]

					# Create the process with gathered data
					self.procs.append(Process(name, size, starts, stops))

		except IOError:
			return False

		return True

	# Load initial memory
	def loadMem(self):
		self.memory = Memory(algorithm)

		for proc in self.procs:
			if proc.starting(0):
				if not self.memory.loadInit(proc):
					self.memory.pprint(0)
					return False

		self.memory.pprint(0)

		return True

	# Run the simulation x steps forward (-1 means do the whole thing)
	def runSim(self, steps):
		# If steps is -1 the simulation is running in quiet mode
		if steps == -1:
			while True:
				change = False

				# Increment simulation time
				self.simTime += 1

				# Check for processes leaving memory
				for proc in self.procs[:]:
					if proc.ending(self.simTime):
						# Remove the ending process from memory
						self.memory.unloadProc(proc)
						change = True

						# If the process has no more cycles we can remove it from our list
						if proc.runCycle == len(proc.starts):
							self.procs.remove(proc)

				# Check for processes entering memory
				for proc in self.procs:
					if proc.starting(self.simTime):
						change = True

						# Attempt to load the process into memory
						if not self.memory.loadProc(proc):
							change = False	# The defrag process will print memory upon completion

							# If we couldn't load the process, try to defrag
							if not self.memory.defrag(proc, self.simTime):
								# If a defrag didn't make enough space, end with an error
								print('ERROR: OUT-OF-MEMORY, ending simulation')
								return

				# If the memory state has changed, print it
				if change:
					self.memory.pprint(self.simTime)

				# If we're out of processes, return
				if len(self.procs) == 0:
					return

		# Otherwise, increment as far as requested
		else:
			for x in range(steps):
				# Increment simulation time
				self.simTime += 1

				# Check for processes leaving memory
				for proc in self.procs[:]:
					if proc.ending(self.simTime):
						# Remove the ending process from memory
						self.memory.unloadProc(proc)

						# If the process has no more cycles we can remove it from our list
						if proc.runCycle == len(proc.starts):
							self.procs.remove(proc)

				# Check for processes entering memory
				for proc in self.procs:
					if proc.starting(self.simTime):
						# Attempt to load the process into memory
						if not self.memory.loadProc(proc):
							# If we couldn't load the process, try to defrag
							if not self.memory.defrag(proc, self.simTime):
								# If a defrag didn't make enough space, end with an error
								print('ERROR: OUT-OF-MEMORY, ending simulation')
								return

			# When everything is done, print the current time and state of the memory
			self.memory.pprint(self.simTime)




# Main Function
if __name__ == '__main__':
	# Verify argument count
	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print('USAGE: %s [-q] <input-file> { noncontig | first | best | next | worst }' % sys.argv[0])
		sys.exit()

	# Check for quiet flag
	if sys.argv[1] == '-q' and len(sys.argv) != 4:
		print('USAGE: %s [-q] <input-file> { noncontig | first | best | next | worst }' % sys.argv[0])
		sys.exit()
	elif sys.argv[1] == '-q':
		quiet = True
		inFile = sys.argv[2]
		algorithm = sys.argv[3]
	else:
		quiet = False
		inFile = sys.argv[1]
		algorithm = sys.argv[2]

	# Make sure the algorithm is valid
	if algorithm not in ['noncontig', 'first', 'best', 'next', 'worst']:
		print('USAGE: %s [-q] <input-file> { noncontig | first | best | next | worst }' % sys.argv[0])
		sys.exit()

	# Read input file and load process information
	procManager = ProcessManager(algorithm)

	# Attempt to load the input file
	if not procManager.loadProcs(inFile):
		print('ERROR: Could not parse input file')
		print('USAGE: %s [-q] <input-file> { noncontig | first | best | next | worst }' % sys.argv[0])
		sys.exit()

	# Load memory
	if not procManager.loadMem():
		print('ERROR: OUT-OF-MEMORY, ending simulation')
		sys.exit()

	# Run simulation
	if quiet:
		procManager.runSim(-1)
		print('Goodbye!')
		sys.exit()
	else:
		response = 1

		while True:
			response = input('Enter t to continue simulation (0 will exit): ')

			if not response.isdigit():
				continue

			response = int(response)

			if response == 0:
				print('Goodbye!')
				sys.exit()

			procManager.runSim(response)







