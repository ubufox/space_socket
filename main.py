import io
import json
import numpy
import pyzed.sl as sl
import sys
import time
import zmq

test_list = [0.0, 0.2, 0.04, 0.8, 0.1, 0.4, 0.4, 0.5, 0.0, 0.95]

def parseArgs(argLen, argv, param):
    if (".svo" in argv):
        # SVO input mode
        param.set_from_svo_file(sys.argv[1])
        print("Sample using SVO file input "+ sys.arg[1])
    elif(len(arv.split(":")) == 2 and len(argv.split(".")) == 4):
        # Stream input mode - IP + port
        l = argv.split(".")
        ip_address = l[0] + '.' + l[1] + '.' + l[2] + '.' + l[3].split(':')[0]
        port = int(l[3].split(':')[1])
        print("Stream input mode")
    elif (len(argv.split(":")) != 2 and len(argv.split(".")) == 4):
        param.set_from_stream(argv)
        print("Stream input mode")
    elif("HD2K" in argv):
        param.camera_resolution = sl.RESOLUTION.HD2K
        print("Using camera in HD2K mode")
    elif("HD1200" in argv):
        param.camera_resolution = sl.RESOLUTION.HD1200
        print("Using camera in HD1200 mode")
    elif("HD1080" in argv):
        param.camera_resolution = sl.RESOLUTION.HD1080
        print("Using camera in HD1080 mode")
    elif("HD720" in argv):
        param.camera_resolution = sl.RESOLUTION.HD720
        print("Using camera in HD720 mode")
    elif("SVGA" in argv):
        param.camera_resolution = sl.RESOLUTION.SVGA
        print("Using camera in SVGA mode")
    elif("VGA" in argv and "SVGA" not in argv):
        param.camera_resolution = sl.RESOLUTION.VGA
        print("Using camera in VGA mode")
         
if __name__ == "__main__":
    print("Running Depth Sensing system")
    print("Initializing ZED sensor...")
    init = sl.InitParameters(
        depth_mode=sl.DEPTH_MODE.PERFORMANCE,
        coordinate_units=sl.UNIT.METER,
        coordinate_system=sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP)

    if len(sys.argv) > 1:
        parseArg(len(sys.argv), sys.argv[1], init)

    print("Setting up ZED camera...")
    zed = sl.Camera()
    status = zed.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        print(repr(status))
        exit()

    res = sl.Resolution()
    res.width = 720
    res.height = 404

    # The Data structure appears to be a 2D array where each array is an array of depth
    # where the index is the x value and y value is the first arrays value

    camera_model = zed.get_camera_information().camera_model

    point_cloud = sl.Mat(res.width, res.height, sl.MAT_TYPE.F32_C4, sl.MEM.CPU)
    print("ZED setup complete!")
   
    print("Setting up message server...")
    ctx = zmq.Context()
    s = ctx.socket(zmq.REP)
    s.bind("tcp://127.0.0.1:5555")
    print("Message server ready!")

    while True:
        try:
            message = s.recv()
            print("Received request: ", message)

            print("Getting ZED point cloud")
            if zed.grab() == sl.ERROR_CODE.SUCCESS:
                print("ZED grab success") 
                try:
                    zed.retrieve_measure(point_cloud, sl.MEASURE.DEPTH, sl.MEM.CPU, res)
                    print("Measure success")
                except Exception as e:
                    print("Failed on retrieve measure")
                    print(e)

                print("Point cloud retrieved!")
                n_data = point_cloud.get_data()
                
                l = list(map(str, n_data.flatten()))
                d = {
                    "resolution": { "width": res.width, "height": res.height },
                    "data": l,
                } 

                print("Sending point cloud... %.4f" % time.perf_counter()) 
                s.send(json.dumps(d).encode("utf-8"))
                print("Point cloud sent! %.4f" % time.perf_counter())
            else:
                print("Failed to grab ZED point cloud")

            time.sleep(0.2)
        except Exception as e:
            print("Shutting down... ")
            print(e)
            zed.close()
            break 
