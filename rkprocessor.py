"""Processes RunKeeper export file 'cardioActivities.csv'

Assumptions:

1. Lowercase of duration key has the prefix 'duration'
2. Lowercase of distance key has the prefix 'distance'
3. Lowercase of date key has the prefix 'date'
4. Dates can be parsed with the strftime format '%Y-%m-%d %H:%M:%S'
5. Distance is measured in kilometers

These assumptions depend on user settings and other pecularities of the RunKeeper app

Non-assumptions:

1. Rows are NOT assumed to be in chronological order
"""
__license__ = "poetic"

from sys import stdin
from datetime import datetime
from argparse import ArgumentParser
from quickcsv import QuickCSV

strptime = datetime.strptime
now = datetime.now
fromtimestamp = datetime.fromtimestamp

def parse_date(date_spec):
	date_formats = [ '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m', '%Y' ]

	for df in date_formats:
		try:
			date = strptime(date_spec, df)
			return date.timestamp()
		except ValueError:
			pass

	raise ValueError('unrecognized date format: {}'.format(date_spec))

def parse_args():
	arg_parser = ArgumentParser()
	arg_parser.add_argument('-', action='store_true', dest='from_stdin', help='read from stdin')
	arg_parser.add_argument('-f', '--filename', default='', help='name of export file')
	arg_parser.add_argument('-s', '--start', default=None, help='start date')
	arg_parser.add_argument('-e', '--end', default=None, help='end date')
	return arg_parser.parse_args()

class RKProcessor():
	def __init__(self, start_timestamp, end_timestamp):
		self.first_activity = None
		self.last_activity = None
		self.total_activities = 0
		self.total_duration = 0 # seconds
		self.total_distance = 0 # meters
		self.warnings = [ ]

		self.start_timestamp = start_timestamp
		self.end_timestamp = end_timestamp

	def __str__(self):
		if self.total_activities:
			str_list = []
			first_date = fromtimestamp(self.first_activity)
			last_date = fromtimestamp(self.last_activity)
			str_list.append('{} - {}'.format(first_date, last_date))
			str_list.append('activities: {}'.format(self.total_activities))
		else:
			return 'no activities'

		if self.total_duration and self.total_distance:
			km = int(self.total_distance // 1000)
			Dm = int(self.total_distance % 1000) // 10
			str_list.append('distance: {}.{:02} km'.format(km, Dm))
			h = int(self.total_duration // 3600)
			m = int(self.total_duration % 3600) // 60
			s = int(self.total_duration % 60)
			str_list.append('duration: {}:{:02}:{:02}'.format(h, m, s))
			pace = int((self.total_duration) / (self.total_distance / 1000))
			str_list.append('average pace: {}:{:02} min/km'.format(pace // 60, pace % 60))
			speed = (self.total_distance / 1000) / (self.total_duration / 3600)
			str_list.append('average speed: {}.{:02} km/h'.format(int(speed), int(100 * (speed % 1.0))))

		if len(self.warnings):
			str_list.append('warnings: {}'.format(self.warnings, ' '.join(self.warnings)))

		return '\n'.join(str_list)

	def warn(self, what, row):
		self.warnings.append('{} (row: {})'.format(what, row))

	def process(self, csvreader):
		csvreader.setup_speed_dials([ 'date', 'duration', 'distance' ])

		for column_date, column_duration, column_distance in csvreader:
			timestamp = strptime(column_date, '%Y-%m-%d %H:%M:%S').timestamp()
			if timestamp >= self.start_timestamp and timestamp <= self.end_timestamp:
				t_l = [0]*3 + column_duration.split(':')
				t_l = t_l[-3:]
				t_h, t_m, t_s = int(t_l[0]), int(t_l[1]), int(t_l[2])
				duration = 3600 * int(t_h) + 60 * int(t_m) + int(t_s)
				if not duration:
					self.warn('duration is zero', row)
				else:
					self.total_duration += duration

				distance = int(1000 * float(column_distance))
				if not distance:
					self.warn('distance is zero', row)
				else:
					self.total_distance += distance

				self.total_activities += 1
				if not self.first_activity or timestamp < self.first_activity:
					self.first_activity = timestamp
				if not self.last_activity or timestamp > self.last_activity:
					self.last_activity = timestamp

if __name__ == '__main__':
	args = parse_args()

	if args.start:
		start_timestamp = parse_date(args.start)
	else:
		start_timestamp = 0

	if args.end:
		end_timestamp = parse_date(args.end)
	else:
		end_timestamp = now().timestamp()

	if args.from_stdin:
		rkfilename = '-'
	else:
		rkfilename = args.filename

	with QuickCSV(rkfilename) as rkreader:
		rkprocessor = RKProcessor(start_timestamp, end_timestamp)
		rkprocessor.process(rkreader)
		print(rkprocessor)
