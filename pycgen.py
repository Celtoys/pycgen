
#
# Copyright 2014 Celtoys Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import sys


#
# Compiles and executes the Python code that the generator code has access to.
# Returns the global python environment that must be used between all code runs in a file.
#
def CreatePythonExecEnvironment():

	prologue = """
import os
import inspect

# Empty string for output
g_EmitOutput = ""


def EmitStr(string):

	globals()["g_EmitOutput"] += string


def EmitLn(line):

	globals()["g_EmitOutput"] += line
	globals()["g_EmitOutput"] += os.linesep


def EmitRepl(generic, repl):

	# Remove leading/trailing newlines
	generic = generic.lstrip(os.linesep)
	generic = generic.rstrip(os.linesep)

	# Split into old value and replacement values
	r = repl.split(":")
	old_val = r[0]
	new_vals = r[1]

	# Iterate all replacement values and emit them
	vals = new_vals.split(",")
	for v in vals:
		EmitLn(generic.replace(old_val, v))

def EmitFmt(line):

	# Get local variables from calling frame
	# This is available in CPython but not guaranteed to be available in other Python implementations
	calling_frame = inspect.currentframe().f_back
	locals = calling_frame.f_locals

	# Remove leading/trailing newlines
	line = line.lstrip(os.linesep)
	line = line.rstrip(os.linesep)

	# Format with the unpacked calling frame local variables
	EmitStr(line.format(**locals))
"""

	# Compile the prologue and return the environment it creates
	exec_globals = { }
	prologue_compiled = compile(prologue, "<prologue>", "exec")
	exec(prologue_compiled, exec_globals)

	return exec_globals


#
# Opens a file and returns it as an array of lines
#
def OpenFile(filename):

	try:
		f = open(filename, "rb")
		lines = f.readlines()
		return lines
	except:
		return None


#
# Strips all leading whitespace on a line and treats it as the indent
#
def GetIndent(line):

	lstrip = line.lstrip()
	indent_size = len(line) - len(lstrip)
	return line[0:indent_size]


#
# Executes python code at runtime within the given environment.
# Assumes that the code will be doing nothing but code emits so returns the
# emit output from the python environment passed in.
#
def ExecPythonLines(lines, filename, start_line, python_env):

	if len(lines) == 0:
		return None

	# Use the indent from the starting line to prepare all the other lines
	start_indent = GetIndent(lines[0])
	indent_size = len(start_indent)

	# Strip leading indentation from all lines
	for i in range(0, len(lines)):
		line = lines[i]

		# Lines that don't share the same indent could be an error...
		if not line.startswith(start_indent):

			# ...unless they're empty lines
			line = line.lstrip()
			if len(line) == 0:
				lines[i] = ""
				continue

			print(filename + "(" + str(start_line + i) + "): Bad leading whitespace indent")
			return None

		lines[i] = line[indent_size:]

	# Run python code with shared global state for entire file
	python_env["g_EmitOutput"] = ""
	code = "".join(lines)
	exec(code, python_env)

	output = python_env["g_EmitOutput"].splitlines()
	if len(output) == 0:
		return None
	# Prefix the output with indentation inferred from the generator
	output = [ start_indent + line for line in output ]
	output = os.linesep.join(output) + os.linesep

	return output


#
# Quick and dirty, line-by-line parsing of an input file looking for Python generator code-blocks
# to execute. Returns the modified file as a set of lines.
#
def ParseInputFile(python_env, filename):

	lines = OpenFile(filename)
	if lines == None:
		return None

	new_lines = [ ]

	in_emit_output = False
	in_python_code = False
	python_lines = [ ]
	python_start_line = 0
	python_indent = 0

	for i in range(0, len(lines)):

		line = lines[i]
		line_lstrip = line.lstrip()

		# Detect and skip start and end of emit output from previous runs
		if line_lstrip.startswith("//$pycgen-begin"):
			in_emit_output = True
			continue
		if in_emit_output and line_lstrip.startswith("//$pycgen-end"):
			in_emit_output = False
			continue

		# Copy lines from old to new, ignoring emit output from previous runs
		if not in_emit_output:
			new_lines.append(line)

		# Detect start of new python code block
		if line_lstrip.startswith("/*$pycgen"):
			in_python_code = True
			python_lines = [ ]
			python_start_line = i + 2	# +1 for skip over "pycgen", +1 for 1-based indexing
			python_indent = GetIndent(line)
			continue

		# Detect end of python code block
		if in_python_code  and line_lstrip.startswith("*/"):
			in_python_code = False

			output = ExecPythonLines(python_lines, filename, python_start_line, python_env)
			if output != None:
				new_lines.append(python_indent + "//$pycgen-begin" + os.linesep)
				new_lines += output
				new_lines.append(python_indent + "//$pycgen-end" + os.linesep)

		# Copy lines in python code blocks
		if in_python_code:
			python_lines.append(line)

	return new_lines


# Parse command-line arguments
if len(sys.argv) != 3:
	print("Use: pycgen.py <input_filename> <output_filename>")
	sys.exit(1)
input_filename = os.path.abspath(sys.argv[1])
output_filename = sys.argv[2]

# Parse the input file and generate any required code
python_env = CreatePythonExecEnvironment()
output_lines = ParseInputFile(python_env, input_filename)
if output_lines == None:
	print("ERROR: Couldn't open file " + input_filename)
	sys.exit(1)

# Write the result
try:
	output_file = open(output_filename, "wb")
	output_file.writelines(output_lines)
except:
	print("ERROR: Couldn't write to file " + output_filename)
	sys.exit(1)
