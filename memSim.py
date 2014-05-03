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
		self.algorithm = algorithm

	def pprint(self, time):
		print('Memory at time %d:' % time)
		for i in range(0, MEM_SIZE, OS_SIZE):
			print(''.join(self.cells[i:i+OS_SIZE]))

	def loadInit(self, proc):
		count = 0
		counting = False

		start = self.cells.index('.')

		for i in range(proc.size):
			location = i + start

			if location >= MEM_SIZE:
				return False

			self.cells[location] = proc.name

		return True

	def loadProc(self, proc):
		pass

	def unloadProc(self, proc):
		self.cells.replace(proc.name, '.')


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
					if proc.ending(simTime):
						# Remove the ending process from memory
						self.memory.unloadProc(proc)
						change = True

						# If the process has no more cycles we can remove it from our list
						if proc.runCycle == len(proc.starts):
							self.procs.remove(proc)

				# Check for processes entering memory
				for proc in self.procs:
					if proc.starting():
						change = True

						# Attempt to load the process into memory
						if not self.memory.loadProc(proc):
							change = False	# The defrag process will print memory upon completion

							# If we couldn't load the process, try to defrag
							if not self.memory.defrag(proc):
								# If a defrag didn't make enough space, end with an error
								print('ERROR: OUT-OF-MEMORY, ending simulation')
								return

				# If the memory state has changed, print it
				if change:
					self.memory.pprint(self.simTime)

		# Otherwise, increment as far as requested
		else:
			for x in range(steps):
				# Increment simulation time
				self.simTime += 1

				# Check for processes leaving memory
				for proc in self.procs[:]:
					if proc.ending(simTime):
						# Remove the ending process from memory
						self.memory.unloadProc(proc)

						# If the process has no more cycles we can remove it from our list
						if proc.runCycle == len(proc.starts):
							self.procs.remove(proc)

				# Check for processes entering memory
				for proc in self.procs:
					if proc.starting():
						# Attempt to load the process into memory
						if not self.memory.loadProc(proc):
							# If we couldn't load the process, try to defrag
							if not self.memory.defrag(proc):
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
	if sys.argv[1] == '-q':
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
		print('ERROR: Could not fit all initial processes in available memory')

	# Run simulation
	if quiet:
		procManager.runSim(-1)
	else:
		response = 1

		while True:
			response = input('Enter t to continue simulation (0 will exit): ')

			if response == 0:
				print('Goodbye!')
				sys.exit()

			procManager.runSim(int(response))







