#!/usr/bin/python
# -*- coding: utf-8 -*-
# Add path to library (just for examples; you do not need this)

ATSIF_SUCCESS = 22002
#ATSIF_DataSource;
ATSIF_Signal     = 0x40000000
ATSIF_Reference  = 0x40000001
ATSIF_Background = 0x40000002
ATSIF_Live       = 0x40000003
ATSIF_Source     = 0x40000004
#ATSIF_StructureElement;
ATSIF_File   = 0x40000000
ATSIF_Insta  = 0x40000001
ATSIF_Calib  = 0x40000002
ATSIF_Andor  = 0x40000000
#ATSIF_ReadMode;
ATSIF_ReadAll        = 0x40000000
ATSIF_ReadHeaderOnly = 0x40000001
#ATSIF_CalibrationAxis;
ATSIF_CalibX        = 0x40000000
ATSIF_CalibY        = 0x40000001
ATSIF_CalibZ        = 0x40000002
#ATSIF_PropertyType;
ATSIF_AT_8         = 0x40000000
ATSIF_AT_U8        = 0x00000001
ATSIF_AT_32        = 0x40000002
ATSIF_AT_U32       = 0x40000003
ATSIF_AT_64        = 0x40000004
ATSIF_AT_U64       = 0x40000005
ATSIF_Float        = 0x40000006
ATSIF_Double       = 0x40000007
ATSIF_String       = 0x40000008

           
class ANDOR_SIF_SPECTRUM():
     
    def __init__(self,fileName):

        import numpy as np
        # import PyQt5
        # import pyqtgraph as pg
        import sys
        # import Class_choose_file as cf
        import ctypes as ct
        self.wavelength = []
        self.spectrum = []
        self.filename = fileName
        #file = cf.Class_choose_file()
        #self.filename = file.name()
        if self.filename.endswith('.sif'):
            self.propNameList = ["FileName","ExposureTime"]
            self.propValueList = []
            self.propTypeList = []
            dll = ct.windll.LoadLibrary(r"ATSIFIO64.dll")
            #ret = ct.c_int()
            ret = ct.c_int()
            noFrames = ct.c_int()
            frameSize = ct.c_int()
            noSubImages = ct.c_int()
            
            atu32_left = ct.c_int()
            atu32_bottom = ct.c_int()
            atu32_right = ct.c_int()
            atu32_top = ct.c_int()
            atu32_hBin = ct.c_int()
            atu32_vBin = ct.c_int()
            
            pixel_calibration = ct.c_double()
           
            MAX_PATH = 255        
            
            ret = dll.ATSIF_SetFileAccessMode(ATSIF_ReadAll) #READ ALL
            if(ret !=ATSIF_SUCCESS):
                print("Could not set File access Mode. Error: %u\n" %ret)
            else:
                
                fileName = ct.create_string_buffer(MAX_PATH)
                for i in range(0,len(self.filename)):
                    #val = int(ord(propName[i]))
                    val = ord(self.filename[i])
                    #print("val = "+str(val))
                    fileName[i] = val
                #filename = "spectrum.sif"
                print("File to open: ")        
                ret = dll.ATSIF_ReadFromFile(ct.byref(fileName))
                #file = 'b'+self.filename
                #ret = dll.ATSIF_ReadFromFile(str(file))
                if(ret != ATSIF_SUCCESS):
                    print("Could not open File : %s.\nError: %d\n" %self.filename %ret)
                else:
                    noFrames = ct.c_int()
                    ret = dll.ATSIF_GetNumberFrames(ATSIF_Signal, ct.byref(noFrames))
                    if(ret != ATSIF_SUCCESS):
                        print("Could not Get Number Frames. Error: %d\n" %ret)
                    else:
                        
                        print("Image contains %d frames.\n" %noFrames.value)
                        ret = dll.ATSIF_GetFrameSize(ATSIF_Signal, ct.byref(frameSize))
                        if(ret != ATSIF_SUCCESS):
                            print("Could not Get Frame Size. Error: %d\n" %ret)
                        else:
                            print("Each frame contains %u pixels.\n" %frameSize.value)
                            ret = dll.ATSIF_GetNumberSubImages(ATSIF_Signal, ct.byref(noSubImages))
                            if(ret != ATSIF_SUCCESS):
                                print("Could not Get Number Sub Images. Error: %d\n" %ret)
                      
                            print("Each frame contains %d sub images.\n" %noSubImages.value)
                            for i in range(0,noSubImages.value):
                                
                                
                                print("SubImage %u Properties:\n" %(i + 1))
                                ret = dll.ATSIF_GetSubImageInfo(ATSIF_Signal,
                                                          i,
                                                          ct.byref(atu32_left),ct.byref(atu32_bottom),
                                                          ct.byref(atu32_right),ct.byref(atu32_top),
                                                          ct.byref(atu32_hBin),ct.byref(atu32_vBin))
                                if(ret != ATSIF_SUCCESS):
                                    print("Could not Get Sub Image Info. Error: %u\n" %ret)
                                else:
                                    print("\t left\t: %d\t bottom\t: %d \n" %(atu32_left.value, atu32_bottom.value))
                                    print("\t right\t: %u\t top\t: %u \n" %(atu32_right.value, atu32_top.value))
                                    print("\t hBin\t: %u\t vBin\t: %u \n" %(atu32_hBin.value, atu32_vBin.value))
                            #imageBuffer  = ct.c_float(frameSize.value)
                            zeros  = np.zeros(frameSize.value, dtype = ct.c_float())
        
                            imageBuffer = (ct.c_float *frameSize.value)(*zeros)
                            
                            ret = dll.ATSIF_GetFrame(ATSIF_Signal, 0, ct.byref(imageBuffer), frameSize.value)
                            if(ret != ATSIF_SUCCESS):
                                print("Could not Get Frame. Error: %u\n" %ret)        
                            else:
                                """
                                print("The first 20 pixel values are : \n")
                                for i in range(0,20):
                                    print("%f\n" %imageBuffer[i])    
                                #print(pixel_calibration.value)
                                """
                                for i in range (1, frameSize.value + 1):
                                    ret = dll.ATSIF_GetPixelCalibration(ATSIF_Signal, ATSIF_CalibX, i, ct.byref(pixel_calibration))
                                    if(ret != ATSIF_SUCCESS):
                                        print("Could not Get Pixel Calibration. Error: %u\n" %ret)        
                                    else:
                                        #print(str(i)+"> "+str(pixel_calibration.value))
                                        self.wavelength.append(pixel_calibration.value)
                                       
                                
        
            sz_propertyName = ct.create_string_buffer(MAX_PATH)
            sz_propertyValue = ct.create_string_buffer(MAX_PATH)
            sz_propertyType = ct.create_string_buffer(MAX_PATH)
            #print("str buffer. "+str(string_buffer))
            #pointer = ct.addressof(string_buffer)
            #print("str buffer pointer. "+str(pointer))
            #propName = 'ATSIF_PROP_EXPOSURETIME\0'
            #propName = "ExposureTime\0"
            for propName in self.propNameList:
                
                for i in range(0,len(propName)):
                    #val = int(ord(propName[i]))
                    val = ord(propName[i])
                    #print("val = "+str(val))
                    sz_propertyName[i] = val
                    #sz_propertyName[i] = propName.encode('utf-8')[i]
                
                #print(type(sz_propertyName))
                #chararray[:] = 0
                
               
                ret = dll.ATSIF_GetPropertyValue(ATSIF_Signal, ct.byref(sz_propertyName), ct.byref(sz_propertyValue), MAX_PATH)
                if(ret != ATSIF_SUCCESS):
                    print("Could not get property value. Error: %u\n" %ret)        
                else:
                    #print(propName +" = "+ str(sz_propertyValue.value))
                    
                    ret = dll.ATSIF_GetPropertyType(ATSIF_Signal, ct.byref(sz_propertyName), ct.byref(sz_propertyType), MAX_PATH)
                    if(ret != ATSIF_SUCCESS):
                        print("Could not get property type. Error: %u\n" %ret)        
                    else:
                        #print(propName +" = "+ str(sz_propertyValue.value)+" "+str(sz_propertyType.value)+".")
                        pass
                
                self.propValueList.append(sz_propertyValue.value)
                self.propTypeList.append(sz_propertyType.value)   
    
            
            #### CLOSING FILE        
            ret = dll.ATSIF_CloseFile()
            if(ret != ATSIF_SUCCESS):
                print("Could not close file. Error: %u\n" %ret.value)        
            else:
                print("File closed.\n")                
            
            #########################
            #self.axis = []
            for j in range(0,len(imageBuffer)):
                self.spectrum.append(imageBuffer[j])
                #self.axis.append(j)
                
        if self.filename.endswith('.txt'):
            
            data = np.genfromtxt(self.filename, skip_header=4, delimiter='\t').transpose()
            self.wavelength = data[0]
            self.spectrum = data[1]
            self.propNameList = ["FileName"]
            self.propValueList = []
            self.propValueList.append(self.filename)
    def get_counts(self):
        return self.spectrum
        
    def get_wavelength(self):
        return self.wavelength
    
    def get_propNameList(self):
        return self.propNameList
    
    def get_propValueList(self):
        return self.propValueList
    
    def get_propTypeList(self):
        return self.propTypeList
        
        
##########################################################
if __name__ == "__main__": #for testing
    app = ANDOR_SIF_SPECTRUM()
    
            
"""            
def run():
    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    app.exec_()
    
run()
"""