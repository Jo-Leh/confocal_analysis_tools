import os
import shutil
import datetime as dt
from threading import Timer

startFold = 'C:/Users/od93yces/'
ls = ['Data', 'Documents', 'Labview', 'Python', 'PycharmProjects']

endFold = 'C:/Users/od93yces/FAUbox/Backup_hard/'

def makeWhatDoTimer():
	now = dt.datetime.now()
	startTime = now.replace(hour=21, minute=0, second=0, microsecond=0)
	if now > startTime:
		startTime += dt.timedelta(days=1)
	secs = (startTime - now).seconds + 1
	print('seconds to next start: {}'.format(secs))
	t = Timer(secs, copyAll)
	t.start()


def copyAll():
	for f in ls:
		if f == 'Documents':
			try:
				shutil.rmtree(endFold + f)
			except Exception as e:
				print(e)
			for fold in os.listdir(startFold + f):
				if os.path.isdir(startFold + f + '/' + fold):
					copy(f + '/' + fold)
				else:
					try:
						shutil.copy2(startFold + f + '/' + fold, endFold + f + '/' + fold)
					except Exception as e:
						print(e)
		else:
			copy(f)
	print('copying finished!')
	makeWhatDoTimer()

def copy(f):
	try:
		if os.path.exists(endFold + f):
			print('deleting old {}'.format(f))
			shutil.rmtree(endFold + f)
		print('copying {}'.format(f))
		shutil.copytree(startFold + f, endFold + f)
	except Exception as e:
		print(e)


if __name__ == '__main__':
	makeWhatDoTimer()




