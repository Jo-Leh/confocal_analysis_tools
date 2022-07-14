import os
import shutil
import datetime as dt

confocalLAPMeas = ['//confocal1/LAP Measurements Data/Johannes', 'confocal_LAP_measurements']

confocalMeas = ['//confocal1/Measurement Data/Johannes', 'confocal_measurements']

folderData = [confocalLAPMeas, confocalMeas]

dataFolder = 'C:/Users/od93yces/Data/'

def datestring():
	return str(dt.datetime.now())

def writCopyLog(text):
	with open('copylog.log', 'a') as f:
		f.write(datestring() + ' > ' + str(text) + '\n')

def compareAge(f1, f2):
	"""returns true if f2 was modified after f1"""
	return os.path.getmtime(f2) > os.path.getmtime(f1)

def copyFolderTree(root_src_dir, root_dst_dir):
	for src_dir, dirs, files in os.walk(root_src_dir):
		dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
		if not os.path.exists(dst_dir):
			os.makedirs(dst_dir)
		for file_ in files:
			src_file = os.path.join(src_dir, file_)
			dst_file = os.path.join(dst_dir, file_)
			if os.path.exists(dst_file):
				# in case of the src and dst are the same file or dst was modified after src
				if os.path.samefile(src_file, dst_file) or compareAge(src_file, dst_file):
					continue
				os.remove(dst_file)
			shutil.copy2(src_file, dst_dir)


def copyData(folders):
	for fold in folders:
		try:
			copyFolderTree(fold[0], dataFolder + fold[1])
		except Exception as e:
			writCopyLog('EXCEPTION!!!\n' + str(e))


if __name__ == '__main__':
	writCopyLog('started copying')
	copyData(folderData)