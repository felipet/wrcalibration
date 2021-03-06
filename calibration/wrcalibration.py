#!   /usr/bin/env   python3
# -*- coding: utf-8 -*
'''
Main class for WR Calibration procedure.

@file
@date Created on Apr 23, 2015
@author Felipe Torres (torresfelipex1<AT>gmail.com)
@copyright LGPL v2.1
@see http://www.ohwr.org/projects/white-rabbit/wiki/Calibration
@ingroup calibration
'''

#------------------------------------------------------------------------------|
#                   GNU LESSER GENERAL PUBLIC LICENSE                          |
#                 ------------------------------------                         |
# This source file is free software; you can redistribute it and/or modify it  |
# under the terms of the GNU Lesser General Public License as published by the |
# Free Software Foundation; either version 2.1 of the License, or (at your     |
# option) any later version. This source is distributed in the hope that it    |
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warrant   |
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser   |
# General Public License for more details. You should have received a copy of  |
# the GNU Lesser General Public License along with this  source; if not,       |
# download it from http://www.gnu.org/licenses/lgpl-2.1.html                   |
#------------------------------------------------------------------------------|

#-------------------------------------------------------------------------------
#                                   Import                                    --
#-------------------------------------------------------------------------------
# Import system modules
import importlib
import time
import datetime

# User defined modules
from main.wrcexceptions import *



class WR_calibration() :
    '''
    Main class for WR Calibration procedure.


    '''
    ## Dictionary to store calibration parameters
    cfg_dict = {}

    ## List to handle connected WR devices
    devices = []

    ## Measurement instrument
    instr = None

    ## Debug output, not handle it directly! Use the methods.
    show_dbg = False

    fibers = ["f1","f2","f1+f2"]

    def __init__(self):
        '''
        Constructor
        '''
        self.cfg_dict['fiber-latency'] = {}
        self.cfg_dict['fiber-latency']['delta1'] = 0
        self.cfg_dict['fiber-latency']['delta2'] = 0

        self.cfg_dict['fiber-asymmetry'] = {}
        self.cfg_dict['port-delay'] = {}

    # ------------------------------------------------------------------------ #

    def enable_dbg(self) :
        '''
        Enable debug output.

        This methods enables all debugging info for the added devices.
        '''
        self.show_dbg = True
        for device in self.devices :
            device.show_dbg = True
        if self.instr != None :
            self.instr.show_dbg = True

    # ------------------------------------------------------------------------ #

    def disable_dbg(self) :
        '''
        Disable debug output.

        This methods disables all debugging info for the added devices.
        '''
        self.show_dbg = False
        for device in self.devices :
            device.show_dbg = False
        if self.instr != None :
            self.instr.show_dbg = False

    # ------------------------------------------------------------------------ #

    def add_wr_device(self, name, device_params) :
        '''
        Method to add a WR device (not calibrated).

        This method use the param name to load a concrete WR device controller \
        from module wr_devices.

        Args:
            name (str) : The name param must be the name of a WR device file \
            located in the folder wr_devices.
            device_params (list) : This variable will be passed to WR device constructor. \
            It is expected that device_params contains 2 items : [interface,port]

        Raises:
            DeviceNotFound if name is not a valid WR device name in wr_devices module.
        '''
        try :
            module = "wr_devices.%s" % name
            if self.show_dbg :
                print("wrcalibration : %s imported" % (module))
            wr_device = importlib.import_module(module)
            name = getattr(wr_device,"__wrdevice__")
            class_ = getattr(wr_device,name)
            self.devices.append(class_(device_params[0],device_params[1]))

        except ImportError as ierr :
            raise DeviceNotFound(ierr.msg)

    # ------------------------------------------------------------------------ #

    def remove_wr_devices(self) :
        '''
        Method to remove all attached WR Devices.
        '''
        if self.show_dbg :
            print("%d devices removed." % len(self.devices))
        for d in self.devices :
            d.close()

        self.devices = []


    # ------------------------------------------------------------------------ #

    def add_meas_instr(self, name, device_params) :
        '''
        Method to add a Measurement instrument.

        This method use the param name to load a concrete Calibration Instrument \
        controller from module calibration.

        Args:
            name (str) : The name param must be the name of a Calibration Instrument \
            controller located in the folder calibration.
            device_params (list) : This variable will be passed to Calibration \
            Instrument constructor. It is expected that device_params contains \
            3 items : [port,master_chan,slave_chan]

        Raises:
            DeviceNotFound if name is not a valid WR device name in wr_devices module.
        '''
        try :
            module = "measurement.%s" % name
            wr_device = importlib.import_module(module)
            name = getattr(wr_device,"__meas_instr__")
            class_ = getattr(wr_device,name)
            self.instr = class_(device_params[0])

        except ImportError as ierr :
            raise DeviceNotFound(ierr.msg)

    # ------------------------------------------------------------------------ #

    def read_config(self, cfg_file) :
        '''
        Method to load a stored calibration configuration from a file.

        This method loads all configuration in the file cfg_file. So any configuration
        in memory will be overwrited. If you want to preserve some measured values
        before read a configuration file you can comment lines in the file with
        "#" or store them to a file using "write_config".

        Args:
            cfg_file(str) : Path to a configuration file.
        '''
        cfg_dict = {}
        flag = 0
        with open(cfg_file, 'r', encoding='utf-8') as cfg :
            for line in cfg :
                # Skip date line
                if line[0] == '#' :
                    continue

                if line[0] == '@' :
                    key = line[1:-1]
                    if key == 'fiber-latency'   : flag = 1
                    if key == 'fiber-asymmetry' : flag = 2
                    if key == 'port-delay'      : flag = 3
                    continue

                if flag == 1 :
                    flag = 0
                    delta1 = float( line.split(" ")[0].split(":")[1] )
                    delta2 = float( line.split(" ")[1].split(":")[1][:-1] )
                    self.cfg_dict['fiber-latency']['delta1'] = delta1
                    self.cfg_dict['fiber-latency']['delta2'] = delta2

                if flag == 2 :
                    for i in line.split(" ") :
                        if i == '\n' : continue
                        k = i.split(":")[0]
                        v = i.split(":")[1]
                        if v[-1] == '\n' :
                            v = v[:-1]
                            flag = 0
                        self.cfg_dict['fiber-asymmetry'][k] = float(v)

                if flag == 3 :
                    for i in line.split(" ") :
                        if i == '\n' : continue
                        k = i.split(":")[0]
                        dtxs = i.split(":")[1].split(",")[0]
                        drxs = i.split(":")[1].split(",")[1]
                        if drxs[-1] == '\n' :
                            drxs = drxs[:-1]
                            flag = 0
                        self.cfg_dict['port-delay'][k] = (float(dtxs), float(drxs))

        print("Configuration loaded.")

    # ------------------------------------------------------------------------ #

    def show_config(self) :
        '''
        Method to show the content of cfg_dict.

        This method prints the values for fiber latency, fiber asymmetry and
        port calibration.
        '''
        print("Fiber latency :")
        print("-- delta1 : %.f2" % self.cfg_dict['fiber-latency']['delta1'])
        print("-- delta2 : %.f2" % self.cfg_dict['fiber-latency']['delta2'])
        print("Fiber asymmetry :")
        for key in self.cfg_dict['fiber-asymmetry'] :
            print("-- %s : %d" % (key,self.cfg_dict['fiber-asymmetry'][key]))
        print("Port delays :")
        for key in self.cfg_dict['port-delay'] :
            print("-- %s : %d,%d" % (key,self.cfg_dict['port-delay'][key][0],\
            self.cfg_dict['port-delay'][key][1]))

    # ------------------------------------------------------------------------ #

    def write_config(self, out_file) :
        '''
        Method to store obtained calibration configuration to a file.

        Args:
            out_file (str) : The name for the output file. If the file exists it
            will be overwrited.
        '''
        with open(out_file, 'w', encoding='utf-8') as out :
            # Write time reference
            now = datetime.datetime.now()
            out.write(now.strftime("#%H:%M %y%m%d\n"))

            out.write("@fiber-latency\n")
            out.write("delta1:%.1f delta2:%.1f\n" % \
            (self.cfg_dict['fiber-latency']['delta1'],self.cfg_dict['fiber-latency']['delta2']))

            out.write("@fiber-asymmetry\n")
            for key in self.cfg_dict['fiber-asymmetry'] :
                out.write("%s:%d " % (key,self.cfg_dict['fiber-asymmetry'][key]))
            out.write("\n")

            out.write("@port-delay\n")
            for key in self.cfg_dict['port-delay'] :
                out.write("%s:%d,%d " % (key,self.cfg_dict['port-delay'][key][0],\
                self.cfg_dict['port-delay'][key][1]))
            out.write('\n')
        print("Configuration stored in ./%s" % out_file)

    # ------------------------------------------------------------------------ #

    def fiber_latency(self, n_samples=10, t_samples=5) :
        '''
        Method to calculate the reference fiber latency.

        This method calculates the fiber delay for a few meters long fiber \
        (delta_1) and for a few kilometers long (delta_2). First fiber will be
        called f1 and second one f2.
        Calculated values where stored in cfg_dict with the key "fiber-latency".

        This method assumes that slave device uses a blue SFP and the master device
        a violet SFP both in the port 1.

        Args:
            n_samples (int) : Indicates how many values will be used for computing \
            stadistics values.
            t_samples (int) : The time between samples.

        Raises:
            WRDeviceNeeded
        '''
        if len(self.devices) < 2 :
            raise WRDeviceNeeded("To measure fiber latency, at least, 2 WR devices are needed.")

        # Assign one device as master and the other as slave
        master = self.devices[0]
        slave = self.devices[1]

        # WR device configuration -----------------------------------

        # First, set all delays and beta values in sfp database to 0
        if self.show_dbg :
            print("Setting initial parameters in WR devices...\n")
            print("Erasing sfp database...")
        master.erase_sfp_config()
        slave.erase_sfp_config()

        if self.show_dbg :
            print("Writing initial configuration to sfp database...")
        slave.write_sfp_config("AXGE-1254-0531",1)
        master.write_sfp_config("AXGE-3454-0531",1)
        master.load_sfp_config()
        slave.load_sfp_config()
        slave.set_slaveport(1)
        master.set_master()


        # Retrieve Round-trip time and bitslide values for both master and slave
        # WR devices when connected by f1, f2 and f1+f2.
        delays_dict = {}
        rtt_dict = {}

        for fiber in self.fibers :
            print("Please connect both WR devices with fiber %s on port 1 and press Enter"\
            % (fiber))
            input()
            print("\nStarting fiber latency measurement procedure.\n")
            time.sleep(1)

            # Wait until servo state in TRANCK PHASE
            if self.show_dbg :
                print("Waiting until TRACK PHASE.....")

            while not slave.in_trackphase() :
                time.sleep(2)

            if self.show_dbg :
                print("Measuring round-trip time (It will take %d s aprox.)..." \
                % (n_samples*t_samples))

            mean_rtt = 0
            for i in range(n_samples) :
                rtt = slave.get_rtt()
                mean_rtt += rtt
                time.sleep(t_samples)
            mean_rtt /= n_samples

            if self.show_dbg :
                print("Mean rtt : %f" % mean_rtt)

            delays_dict[fiber] = slave.get_phy_delays()
            rtt_dict[fiber] = mean_rtt

        # As Rx delays are set to 0 in sfp database, the stat values for Rx
        # are the bitslides
        delay_mm1 = rtt_dict['f1'] - delays_dict['f1']['master'][1] - delays_dict['f1']['slave'][1]
        delay_mm2 = rtt_dict['f2'] - delays_dict['f2']['master'][1] - delays_dict['f2']['slave'][1]
        delay_mm3 = rtt_dict['f1+f2'] - delays_dict['f1+f2']['master'][1] - delays_dict['f1+f2']['slave'][1]

        if self.show_dbg :
            print("delay_mm1 : %f" % delay_mm1)
            print("delay_mm2 : %f" % delay_mm2)
            print("delay_mm3 : %f" % delay_mm3)

        delta1 = delay_mm3 - delay_mm2
        delta2 = delay_mm3 - delay_mm1

        self.cfg_dict['fiber-latency']['delta1'] = delta1
        self.cfg_dict['fiber-latency']['delta2'] = delta2
        print("Fiber latency : delta1 = %.2f , delta2 = %.2f" % (delta1,delta2))

    # ------------------------------------------------------------------------ #

    def fiber_asymmetry(self, n_samples=10, t_samples=5, port = 1, sfp = "blue") :
        '''
        Method to calculate the fiber asymmetry.

        This method calculates the asymmetry for a
        This method calculates the fiber asymmetry for a few meters long fiber \
        (delta_1) and for a few kilometers long (delta_2). First fiber will be
        called f1 and second one f2.
        Calculated values where stored in cfg_dict with the key "fiber-latency".

        Args:
            n_samples (int) : Indicates how many values will be used for computing \
            stadistics values.
            t_samples (int) : The time between samples.
            port (int) : The port used for connecting master to slave.
            sfp (str) : Indicates which sfp is used in WR slave device.

        Raises:
            WRDeviceNeeded if no WR devices are added.
            MeasuringError if a time interval value is higher than expected.
            FiberLatencyNeeded if no previous fiber latency measure is done.
            MeasurementInstrumentNeeded if no instruments are added.
        '''
        if len(self.devices) < 2 :
            raise WRDeviceNeeded("To measure fiber latency, at least, 2 WR devices are needed.")

        if self.instr == None :
            raise MeasurementInstrumentNeeded("To measure skew between PPS signals a measurement instrument must be added.")

        if self.cfg_dict['fiber-latency']['delta1'] == 0 :
            raise FiberLatencyNeeded("A valid fiber latency values is needed to use this method.")

        # Assign one device as master and the other as slave
        master = self.devices[0]
        slave = self.devices[1]

        # WR device configuration -----------------------------------

        # First, set all delays and beta values in sfp database to 0
        if self.show_dbg :
            print("Setting initial parameters in WR devices...\n")
            print("Erasing sfp database...")
        master.erase_sfp_config()
        slave.erase_sfp_config()

        if sfp == "blue" :
            sfp_sn1 = "AXGE-1254-0531"
            sfp_sn2 = "AXGE-3454-0531"

        else :
            sfp_sn1 = "AXGE-3454-0531"
            sfp_sn2 = "AXGE-1254-0531"

        if self.show_dbg :
            print("Writing initial configuration to sfp database...")
        slave.write_sfp_config(sfp_sn1,port)
        master.write_sfp_config(sfp_sn2,port)
        master.load_sfp_config()
        slave.load_sfp_config()
        slave.set_slaveport(port)
        master.set_master()

        # Measure delay between the PPS signals
        skew = []

        for fiber in self.fibers :
            if fiber == 'f1+f2' : continue

            print("Please connect both WR devices with fiber %s and press Enter" % (fiber))
            input()
            print("Now connect their PPS outputs to the measurement instrument and press Enter")
            input()
            print("\nStarting fiber latency measurement procedure.\n")
            time.sleep(1)

            # Wait until servo state in TRANCK PHASE
            if self.show_dbg :
                print("Waiting until TRACK PHASE.....")

            while not slave.in_trackphase() :
                time.sleep(2)

            print("Measuring skew between PPS signals, it should take a long time...")
            mean_skew = self.instr.mean_time_interval(n_samples, t_samples)
            # Change the sign when using blue SFP
            if sfp == "blue" :
                mean_skew *= -1
            if mean_skew >= 1e-6 :
                raise MeasuringError("Time interval between input 1 and 2 is more than expected. Are the input channels adequately connected?")
            skew.append(mean_skew)

        # Calculate alpha and alpha_n -------------------------

        # Pass time measures from s to ps
        skew[0] = skew[0] * 1e12
        skew[1] = skew[1] * 1e12
        if self.show_dbg :
            print("Mean skew master to slave with f1: %G" % skew[0])
            print("Mean skew master to slave with f2: %G" % skew[1])

        dif = skew[1] - skew[0]
        delta_1 = self.cfg_dict['fiber-latency']['delta1']
        delta_2 = self.cfg_dict['fiber-latency']['delta2']
        alpha = ( 2 * dif ) / ( 0.5 * delta_2 - dif )
        alpha_n = pow(2,40) * ( ((alpha+1)/(alpha+2)) - 0.5 )
        # When measuring with violet sfp in the slave device, it's needed change the sign
        if sfp == "violet" : alpha_n = alpha_n * -1
        self.cfg_dict['fiber-asymmetry']["%s-wr%d"%(sfp,port)] = alpha_n
        print("Fiber asymmetry value for port %d and sfp %s = %d" % (port,sfp,alpha_n))

    # ------------------------------------------------------------------------ #

    def calibrate_device_port(self, error, n_samples=10, t_samples=5, port = 1, sfp = "blue") :
        '''
        Method to calibrate a port for a WR device.

        This method will measure time delay between the PPS of a WR Device previously
        calibrated and the PPS of a uncalibrated device and will calculate Rx and
        Tx delay values.

        A WR Calibrator is needed, also you must use a fiber with latency and
        asymmetry parameters known.
        Remove WR devices associated to the program before calling this method.
        Use remove_wr_devices().

        Args:
            error (float) : The minimal time difference accepted (in ps). It will depend of the \
            measuring instrument.
            n_samples (int) : Indicates how many values will be used for computing \
            stadistics values.
            t_samples (int) : The time between samples.
            port (int) : The port used for connecting master to slave.
            sfp (str) : Indicates which sfp is used in WR slave device.

        Raises:
            WRDeviceNeeded if a slave device is not connected.
            ValueError if master_chan or slave_chan of the instrument are not set.
            TriggerNotSet if trigger levels are not set.
            MeasuringError if a time interval value is higher than expected.
            FiberLatencyNeeded if no previous fiber latency measure is done.
            FiberAsymmetryNeeded if no previous fiber asymmetry measure is done.
        '''
        if len(self.devices) < 1 :
            raise WRDeviceNeeded("To measure fiber latency, at least, 2 WR devices are needed.")

        if self.instr == None :
            raise MeasurementInstrumentNeeded("To measure skew between PPS signals a measurement instrument must be added.")

        if self.cfg_dict['fiber-latency']['delta1'] == 0 :
            raise FiberLatencyNeeded("A valid fiber latency values are needed to use this method.")

        key = "%s-wr%d"%(sfp,port)
        if key not in self.cfg_dict['fiber-asymmetry'] :
            raise FiberLatencyNeeded("Fiber asymmetry value for port %d and sfp %s is needed." % (port,sfp))

        # Assign the device that will be calibrated
        slave = self.devices[0]

        # WR device configuration -----------------------------------

        # First, set dTx and Rx to 0, and beta to a previously measured value.
        if self.show_dbg :
            print("Setting initial parameters in WR devices...\n")
            print("Erasing sfp database...")
        slave.erase_sfp_config()

        if self.show_dbg :
            print("Writing initial configuration to sfp database...")
        if sfp == "blue" :
            sfp_sn = "AXGE-1254-0531"
        else : sfp_sn = "AXGE-3454-0531"
        key = "%s-wr%d"%(sfp,port)
        beta = self.cfg_dict['fiber-asymmetry'][key]
        slave.write_sfp_config(sfp_sn, port, 0, 0, beta)
        slave.load_sfp_config()
        slave.set_slaveport(port)

        input("Pleasse connect the WR calibrator to the uncalibrated device with fiber f1 and press Enter")
        print("\nStarting device calibration procedure.\n")
        # Wait until servo state in TRANCK PHASE
        if self.show_dbg :
            print("Waiting until TRACK PHASE.....")
        while not slave.in_trackphase() :
            time.sleep(2)

        if self.show_dbg :
            print("Calculating coarse Tx and Rx delays ...")
        mean_rtt = 0
        for i in range(n_samples) :
            rtt = slave.get_rtt()
            mean_rtt += rtt
            time.sleep(t_samples)
        mean_rtt /= n_samples

        delays_dict = slave.get_phy_delays()
        dtxm = delays_dict['master'][0]
        drxm = delays_dict['master'][1]
        bitslide = delays_dict['slave'][1]
        delta1 = self.cfg_dict['fiber-latency']['delta1']

        coarse_delays = 0.5 * ( mean_rtt - dtxm - drxm - bitslide - delta1 )

        slave.erase_sfp_config()
        slave.write_sfp_config(sfp_sn, port, coarse_delays, coarse_delays, beta)
        slave.load_sfp_config()

        if self.show_dbg :
            print("Coarse transmission and reception delays = %d" % coarse_delays)
        print("Calibrating device ...")

        # Keep adjusting delays, while the skew is higher than error.
        # A iteration limit is set for avoiding a infinite loop.
        times = 10
        i = 0
        mean_skew = 1e10
        old_dtxs = coarse_delays
        old_drxs = coarse_delays

        while abs(mean_skew) > error and i < times:
            # Wait until servo state in TRANCK PHASE
            if self.show_dbg :
                print("Waiting until TRACK PHASE.....")

            while not slave.in_trackphase() :
                time.sleep(2)

            print("Measuring skew between PPS signals, it should take a long time...")
            mean_skew = self.instr.mean_time_interval(n_samples, t_samples)

            # Write the new delay value
            # mean_skew must be in ps
            mean_skew *= 1e12
            print("skew = %f" % mean_skew)
            dtxs = old_dtxs - mean_skew
            drxs = old_drxs + mean_skew

            if self.show_dbg :
                print("Writing current delays %d,%d to sfp database..." % (dtxs,drxs))
            slave.erase_sfp_config()
            slave.write_sfp_config(sfp_sn, port, dtxs, drxs, beta)
            slave.load_sfp_config()
            old_dtxs = dtxs
            old_drxs = drxs

            i += 1

        if self.show_dbg and i == times:
            print("Exceeded limit of iterations")

        # Store measured delay values
        self.cfg_dict['port-delay'][key] = (dtxs,drxs)
        print("Port calibrated.")
        if self.show_dbg :
            print("dtxs = %d , drxs = %d, final skew = %f" % (dtxs,drxs,mean_skew))
