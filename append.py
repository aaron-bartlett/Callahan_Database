import csv

with open("temp_songs.csv", 'a', newline='') as songsfile:
	wr = csv.writer(songsfile)
	with open("temp_songs_409.csv", 'r', newline='') as two:
		sec = csv.reader(two)
		for row in sec: 
			wr.writerow(row)
	with open("temp_songs_499.csv", 'r', newline='') as two:
		sec = csv.reader(two)
		for row in sec: 
			wr.writerow(row)
	with open("temp_songs_596.csv", 'r', newline='') as two:
		sec = csv.reader(two)
		for row in sec: 
			wr.writerow(row)
