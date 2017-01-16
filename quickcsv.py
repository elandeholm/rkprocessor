"""Quick CSV file reader

Features:

1. Context manager
2. Iteration
3. Column name rewrite
4. Case insensitive prefix matching on column names
5. Column values via user controlled speed dials accessor, no per row dict lookups 
6. automatically uses sys.stdin if filename is '-'

Usage:

with QuickCSV(filename) as csvreader:
	csvreader.setup_speed_dials(list_of_speed_dials)
	OR
	csvreader.setup_speed_dials(list_of_speed_dials, column_rename_dict)

	for row in csvreader():
		these, are my, columns = row
		do something...

Example:

with QuickCSV(filename) as csvreader:
	csvreader.setup_speed_dials([ id name address ],  { 'identifier': 'id', 'user_name': name, 'address line': 'address'})
	for id, name, address in csvreader():
		...
"""
__license__ = "poetic"

import csv
import sys

class QuickCSV():
	def __init__(self, filename=None, file_obj=None):
		self.filename = filename
		self.file_obj = file_obj

	def __iter__(self):
		return self

	def __next__(self):
		row = next(self.readeriter)
		return [ row[index] for index in self.accessor ]

	def __enter__(self):
		if self.filename == '-' and not self.file_obj:
			self.file_obj = sys.stdin
		elif self.filename:
			self.file_obj = open(self.filename, 'r')

		self.csvreader = csv.reader(self.file_obj)
		self.readeriter = iter(self.csvreader)

		self.columns = next(self.readeriter)
		self.enumerated_columns = { i: c for i, c in enumerate(self.columns) }
		self.columns_to_index = { c: i for i, c in enumerate(self.columns) }

		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		# don't close stdin
		if self.file_obj and self.file_obj != sys.stdin:
			self.file_obj.close()

	def __str__(self):
		str_list = [ ]
		str_list.append('filename: {}'.format(self.filename))
		str_list.append('file_obj: {}'.format(self.file_obj))
		str_list.append('csvreader: {}'.format(self.csvreader))
		str_list.append('readeriter: {}'.format(self.readeriter))
		str_list.append('columns: {}'.format(self.columns))
		str_list.append('enumerated_columns: {}'.format(self.enumerated_columns))
		str_list.append('columns_to_index: {}'.format(self.columns_to_index))
		str_list.append('speed_dials: {}'.format(self.speed_dials))
		str_list.append('accessor: {}'.format(self.accessor))
		return '\n'.join(str_list)

	def setup_speed_dials(self, speed_dials, column_rename=None):
		self.speed_dials = { }

		if column_rename:
			# using a column_rename dict, we can rename non-machine readable
			# columns like 'Distance (km)' to 'distance'
			for column_name, pattern in column_rename.items():
				try:
					self.speed_dials[pattern] = self.columns_to_index[column_name]
				except KeyError:
					raise ValueError('no match for column: "{}"'.format(column_name))
		else:
			# if no column_rename dict is given, try a relaxed case insensitive
			# prefix match with the speed dial patterns on the column names
			for pattern in speed_dials:
				matching_index = None
				for index, column_name in self.enumerated_columns.items():
					if column_name.lower().startswith(pattern):
						matching_index = index
						break
				if matching_index is None:
					raise ValueError('no match for pattern: "{}"'.format(pattern))

				self.speed_dials[pattern] = matching_index

		self.setup_accessor(speed_dials)

	def setup_accessor(self, speed_dials):
		self.accessor = [ ]
		for pattern in speed_dials:
			if pattern in self.speed_dials:
				self.accessor.append(self.speed_dials[pattern])
			else:
				raise ValueError('no match for speed dial "{}" '.format(pattern))
