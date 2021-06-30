import serial
import json
import paramiko
import os
import sys
import time
import re
import logging

'''
PBC SSH Driver v2021-0620-r1
'''


class PBC_Ser(object):

    def __init__(self, serial_comport: str):
        self.serialcom = serial.Serial(serial_comport, 115200)

    def send_data(self, data_out: str):
        self.data = data_out
        self.serialcom.write(self.data.encode())
        time.sleep(.1)

    def close(self):
        self.serialcom.close()
        time.sleep(.1)

    def enable_ssh(self):
        # last_ip = input('Input last IP address in hex <xxxx> for UUT:')
        # while not last_ip:
        #     last_ip = input('Input last IP address in hex <xxxx> for UUT:')
        self.pbc_console_login()
        self.pbc_console_exit()
        print(f'Please wait, exiting PBC console...')
        # self.send_data("\r")
        # time.sleep(1)
        # self.send_data("\r")
        # time.sleep(.5)
        self.send_data("root\r")
        time.sleep(.5)
        self.send_data("root\r")
        time.sleep(1)
        self.send_data("ip addr add fe80::ffd2:8387:281b:1074/255.255.255.0 dev br0\r")
        time.sleep(1)
        print(f'Your PBC IP address is: fe80::ffd2:8387:281b:1074')

    def enable_ssh_2(self):
        # last_ip = input('Input last IP address in hex <xxxx> for UUT:')
        # while not last_ip:
        #     last_ip = input('Input last IP address in hex <xxxx> for UUT:')
        # self.pbc_console_login()
        # self.pbc_console_exit()
        # self.pbc_console_exit()
        # self.pbc_console_exit()
        print(f'Please wait, exiting PBC console...')
        self.send_data("admin\r")
        time.sleep(1)
        self.send_data("config\r")
        time.sleep(.5)
        self.send_data("sudo -s\r")
        time.sleep(.5)
        self.send_data("config\r")
        time.sleep(1)
        self.send_data("ip addr add fe80::ffd2:8387:281b:1074/255.255.255.0 dev br0\r")
        time.sleep(1)
        print(f'Your PBC IP address is: fe80::ffd2:8387:281b:1074')

    def pbc_console_login(self):
        self.send_data('root\r')
        self.send_data('root\r')

    def pbc_console_exit(self):
        self.send_data('\x03')  # send ctrl + c key
        self.send_data('exit\r')
        time.sleep(9)  # Must wait for console exit

    def enter_chassis_shell(self):
        self.send_data("chassis-shell\r")

    def exit_chassis_shell(self):
        self.send_data('\x03')  # send ctrl + c key

    def return_chassis_shell_root(self):
        self.send_data('/\r')  # send ctrl + c key


class PBC_SSH(object):

    def __init__(self, addr: str):
        # self.port = 22
        # self.user = 'root'
        # self.password = 'root'
        # self.timeout = 23
        self.response = str()
        self.match = str()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(addr, 22, 'root', 'root')
        self.channel = self.ssh.invoke_shell()
        self._logger = logging.getLogger(self.__class__.__name__)

    def pbc_comm_test(self):
        """performing this test will login to chassis-shell CLI"""
        if self.process_channel("chassis-shell\r").find("/>") == -1:
            return False
        else:
            return True

    def pbc_end_connection(self):
        self.ssh.close()

    def json_from_s(self, s):
        self.match = re.findall(r"{.+[:,].+}|\[.+[,:].+\]", s)
        return json.loads(self.match[0]) if self.match else None

    def process_channel(self, input):
        self.channel_data = str()
        self.host = str()
        self.scrfile = str()
        time.sleep(.5)
        self.channel.send(input)
        time.sleep(1.5)
        if self.channel.recv_ready():
            self.channel_data += str(self.channel.recv(9999).decode("utf8"))
        # print(self.channel_data)
        self._logger.info(self.channel_data)
        return self.channel_data

    # ######################### Communication Test ###########################

    def can_dump(self):
        self.process_channel("candump can0 | grep 7[0-9]\r")
        time.sleep(5)
        self.process_channel("\x03")

    # ######################### EMB Tests ###########################
    def pbc_console_login_old(self):
        self.process_channel('root\r')
        self.process_channel('root\r')

    def pbc_console_login(self):
        # self.process_channel('admin\r')
        # time.sleep(.5)
        # self.process_channel('config\r')
        # time.sleep(.5)
        self.process_channel('sudo -s\r')
        time.sleep(.5)
        self.process_channel('config\r')

    def pbc_console_exit(self):
        self.process_channel('\x03')  # send ctrl + c key
        self.process_channel('exit\r')

    def enter_chassis_shell(self):
        self.process_channel("chassis-shell\r")

    def exit_chassis_shell(self):
        self.process_channel('\x03')  # send ctrl + c key

    def return_chassis_shell_root(self):
        self.process_channel('/\r')  # send ctrl + c key

    def platform_sw_version(self):
        self.process_channel("/\r")
        self.process_channel("/Platform\r")
        self.process_channel("/PowerMonitor/board-rev\r")

    def init_all_can(self, evt: bool):  # Include the PM --no-detect bypass, must remove for DVT
        self.process_channel("CCB can0\r")
        self.process_channel("AUXPS can0\r")
        self.process_channel("/PM\r")
        if evt: self.pm_no_detect()
        for i in range(1, 6):
            self.process_channel('/PM/PM' + str(i) + ' can0\r')

    def init_all_pm(self):
        self.process_channel('/\r')
        self.process_channel('/PM\r')
        for i in range(1, 6):
            self.process_channel('PM' + str(i) + ' can0\r')

    def pm_init(self, pm):
        self.process_channel('/\r')
        self.process_channel('/PM\r')
        self.process_channel('PM' + str(pm) + ' can0\r')
        print(f'\nWating for PM{pm} to come online...')
        time.sleep(6)

    def get_temps(self):
        self.process_channel("/\r")
        self.process_channel("/TempSensor/TEMP1\r")
        self.process_channel("/CCB/temps\r")
        time.sleep(1)
        self.process_channel("/AUXPS/temps\r")
        time.sleep(1)
        self.process_channel("/PowerMonitor/temp 0\r")  # Powermonitor read DRY-Zone RTD temp read on C
        time.sleep(1)

    def toggle_all_pm(self):
        self.process_channel("/\r")
        for i in range(1, 6):
            self.process_channel('/PM/PM' + str(i) + ' op\r')
        time.sleep(.5)

    def show_pm_status(self, pm):
        self.process_channel("/\r")
        self.process_channel("/PM\r")
        self.process_channel("PM" + str(pm) + "\r")

    # ################### PBC LV Tests #########################
    def ext_chassis_led(self, r, g):
        if r == 1:
            self.process_channel("/ExtChassisLed/RED1 1\r")  # Set GREEN ON
        if r == 0:
            self.process_channel("/ExtChassisLed/RED1 0\r")  # Set GREEN ON
        if g == 1:
            self.process_channel("/ExtChassisLed/GREEN1 1\r")  # Set GREEN ON
        if g == 0:
            self.process_channel("/ExtChassisLed/GREEN1 0\r")  # Set GREEN ON

    def dry_zone_fan(self, fan, speed, enable):
        self.process_channel("/Fan/DRY-Zone-" + str(fan) + "\r")  # Enter PBC Fan directory
        self.process_channel("speed " + str(speed) + "\r")  # Set PBC Fan speed
        time.sleep(1.5)
        self.process_channel("power " + str(enable) + "\r")  # Set PBC Fan enable
        time.sleep(1.5)
        self.process_channel("\r")  # Status PBC Fan

    def dry_zone_one_fan_ctrl(self, fan, sp_else_pwr, enable):
        self.process_channel("/Fan/DRY-Zone-" + str(fan) + "\r")  # Enter PBC Fan directory
        if sp_else_pwr:
            sp = "100" if enable else "0"
            self.process_channel("speed " + str(sp) + "\r")  # Set PBC Fan speed
        time.sleep(.25)
        if not sp_else_pwr:
            self.process_channel("power " + str(enable) + "\r")  # Set PBC Fan enable
            time.sleep(.25)
        self.process_channel("\r")  # Status PBC Fan
        # time.sleep(.5)

    def dry_zone_fan_current(self, fan):  # DRY-Zone fan currents Powermonitor read DRY-Zone fan 1 and 2
        self.process_channel("/PowerMonitor/fan " + str(fan) + "\r")  # Powermonitor read DRY-Zone fan 1

    def gpio_expander(self):
        self.process_channel("/\r")
        self.process_channel("/GpioExpander\r")  # Read GpioExpander status

    def safety_sw(self, category):
        self.process_channel("/Reed\r")
        if category == 'thermal':
            self.process_channel("/ThermalSw\r")  # Read ThermalSw status
        if category == 'reed':
            self.process_channel("/Reed\r")
        if category == 'reed1':
            self.process_channel("REED1-DoorWetBoxFront\r")
        if category == 'surge':
            self.process_channel("/SurgeDet\r")

    # def pm_present_can_id():
    #     toggle_all_pm()
    #     show_pm_status()

    # CCB Tests
    def ccb_init(self):
        self.process_channel('\x03')  # send ctrl + c key
        self.enter_chassis_shell()
        self.process_channel("/CCB can0\r")
        time.sleep(1)
        # self.process_channel("/CCB op\r")

    def ccb_info(self):
        self.process_channel("/\r")
        self.process_channel("/CCB\r")

    def ccb_read_logs(self):  #
        self.process_channel(".quit\r")
        self.process_channel("cat /var/log/CCB-selftest.log\r")  # read dump

    def ccb_bl_fw_version(self):
        self.process_channel("/CCB/bootversion\r")
        self.process_channel("/CCB/appversion\r")

    def ccb_fault_info(self):
        self.process_channel("/CCB/faultInfo\r")

    def ccb_fan_bank_info(self, fanBank):
        if fanBank == 1:
            self.process_channel("/CCB/fanBank1\r")
        if fanBank == 2:
            self.process_channel("/CCB/fanBank2\r")
        if fanBank == 3:
            self.process_channel("/CCB/fanBank3\r")

    def ccb_pump_info(self):
        self.process_channel("/CCB/pump\r")

    def ccb_self_test(self):  # must run before trying to poll for CCB faults in ccb_fault_info()
        self.process_channel("/CCB/selfTest\r")

    def ccb_coolant_level(self):  # must run while filling up coolant tank
        self.process_channel("/CCB/coolantLevel\r")

    def ccb_fan_speed(self, b_num, f_speed):  # <bank_number> <speed 0-100> set fan-bank speed
        self.process_channel("/CCB/fanspeed " + str(b_num) + " " + str(f_speed) + "\r")  # Set CCB Fan speed
        time.sleep(1)

    def ccb_pump_speed(self, p_speed):  # <speed 0-100> set pump speed
        self.process_channel("/CCB/pumpspeed " + " " + str(p_speed) + "\r")  # Set CCB pump speed
        time.sleep(1)

    # Close Loop Thermal Control
    def autoThermal(self, poll, log_freq):  # <bank_number> <speed 0-100> set fan-bank speed
        self.process_channel("/PowerBlock/autoThermal  " + str(poll) + "\r")  # Set to close loop and poll freq
        time.sleep(1)
        self.process_channel("/PowerBlock/logInfo  " + str(log_freq) + "\r")  # Set to log freq in sec, default 5 sec
        time.sleep(1)

    # AUXPS Tests
    def auxps_info(self):
        # self.process_channel("/\r")
        self.process_channel("/AUXPS\r")

    def auxps_init(self):
        self.process_channel("/\r")
        self.process_channel("/AUXPS can0\r")

    def auxps_read_logs(self):  #
        self.process_channel(".quit\r")
        time.sleep(1)
        self.process_channel("cat /var/log/AuxPS-selftest.log\r")  # read dump

    def auxps_remove_logs(self):  #
        self.process_channel(".quit\r")
        time.sleep(1)
        self.process_channel("rm -v /var/log/AuxPS-selftest.log\r")  # read dump

    def auxps_bl_fw_version(self):
        self.process_channel("/AUXPS/bootversion\r")
        self.process_channel("/AUXPS/appversion\r")

    def auxps_fault_info(self):
        self.process_channel("/AUXPS/faults\r")

    def auxps_bank_info(self, auxBank):
        if auxBank == 'ccb':
            return self.json_from_s(self.process_channel("/AUXPS/CCBChannel\r"))
        if auxBank == 'pbc':
            return self.json_from_s(self.process_channel("/AUXPS/PBCChannel\r"))
        if auxBank == 'ext':
            return self.json_from_s(self.process_channel("/AUXPS/ExtChannel\r"))
        if auxBank == 'input':
            return self.json_from_s(self.process_channel("/AUXPS/InputChannel\r"))

    def auxps_channel_ctrl(self, ch: str, set_to: str):  # <ccb|pbc|ext> <0-3> 0:enable, 1:disable
        self.process_channel(f"/AUXPS/channelCtrl {ch} {set_to}\r")
        if ch == 'ccb':
            return self.json_from_s(self.process_channel("/AUXPS/CCBChannel\r"))
        if ch == 'pbc':
            return self.json_from_s(self.process_channel("/AUXPS/PBCChannel\r"))
        if ch == 'ext':
            return self.json_from_s(self.process_channel("/AUXPS/ExtChannel\r"))

    def auxps_self_test(self):  # must run before trying to poll for AUXPS faults in AUXPS_fault_info()
        self.process_channel("/AUXPS/selfTest\r")

    def auxps_shunt_ctrl(self, s_state):  #
        self.process_channel("/AUXPS/shuntControl " + str(s_state) + "\r")

    def auxps_fan_speed(self, af_speed):  # <speed 0-100> set fan speed
        return self.json_from_s(self.process_channel("/AUXPS/fanspeed " + str(af_speed) + "\r"))  # Set AUXPS Fan speed

    def auxps_fan_info(self):  # <speed 0-100>, <rpm>
        # self.response = self.process_channel("/AUXPS/fanstatus\r")  # SGet auxps Fan speed
        # time.sleep(1)
        # return self.json_from_s(self.response)
        return self.json_from_s(self.process_channel("/AUXPS/fanstatus\r"))  # SGet auxps Fan speed

    def auxps_autoPowerCycle(self, seconds):  # <seconds> Set auto power-cycle timeout on CAN/HB miss (current: 0sec)
        self.process_channel("/AUXPS/autoPowerCycle " + str(seconds) + "\r")  #
        time.sleep(1)

    def auxps_temps(self, humidity=False, dewpoint=False):
        # self.process_channel("/AUXPS/temps\r")  #
        # time.sleep(1)
        if humidity: self.process_channel("/AUXPS/humidity\r")  #
        if dewpoint: self.process_channel("/AUXPS/dewpoint\r")  #
        return self.json_from_s(self.process_channel("/AUXPS/temps\r"))

    def auxps_input_channel_info(self):  # show all 3x input channels
        return self.json_from_s(self.process_channel("/AUXPS/InputChannel\r"))

    # PM Power Control
    def pm_no_detect(self):  #
        self.process_channel("/\r")
        self.process_channel("/PM\r")
        self.process_channel("--no-detect\r")  # set PBC to no MPx GPIO pin detect
        time.sleep(1)

    def pm_bl_fw_version(self, pm):
        self.process_channel("/PM/PM" + str(pm) + "/bootversion\r")
        self.process_channel("/PM/PM" + str(pm) + "/appversion\r")

    # def pm_pwr_ctrl(self, pm, bus, volts, amps):  # <a|b|0> <volts> <amps> [maxvolts]    Set pm output bus/volts/amps
    #     self.process_channel("/PM/PM" + str(pm) + "/setTargets " + str(bus) + " " + str(volts) + " " + str(amps) + "\r")
    #     time.sleep(1)

    def pm_pwr_ctrl(self, pm, bus, volts, amps):  # <a|b|0> <volts> <amps> [maxvolts]    Set pm output bus/volts/amps
        self.process_channel("/\r")
        self.process_channel(f"/PM/PM{pm}\r")
        # self.process_channel("/PM/PM" + str(pm) + " \r")
        self.process_channel(f"setTargets {bus} {volts} {amps}\r")
        time.sleep(2)
        self.process_channel("\r")
        self.process_channel("/\r")

    #### BK Test
    def bk_pwr_ctrl(self, state):
        # self._res_manager.write(b"OUTPut ON\r\n")
        if state == 1:
            self.process_channel("OUTPut ON\n")
        if state == 0:
            self.process_channel("OUTPut OFF\n")
        time.sleep(1)

    # Burn-in test
    def pb_bi_test(self, bus: str, volts: str, amps: str, pm1_5: bool):
        if pm1_5:
            power_kw = '200'  # set 200kW max power if PM 1.5
        else:
            power_kw = '156'
        self.pbc_console_login()
        self.enable_ssh()
        time.sleep(1)
        self.process_channel(f"test-pnode -r {bus} {power_kw}\r")  #
        time.sleep(1)
        self.process_channel(f"test-pnode {bus} {volts} {amps}\r")  # < a | b > < powerkw >
        time.sleep(1)


class PBC_SSH_2(object):
    """A copy of PBC_SSH with the addition of login password support for EMB plat version > 177  """

    def __init__(self, addr: str, user='admin', password='config'):
        # self.port = 22
        # self.user = 'root'
        # self.password = 'root'
        # self.timeout = 23
        self.response = str()
        self.match = str()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(addr, 22, user, password)
        self.channel = self.ssh.invoke_shell()
        self._logger = logging.getLogger(self.__class__.__name__)

    def pbc_file_transfer(self, localpath='none', targetpath='none', direction='up'):
        sftp = self.ssh.open_sftp()
        if direction == 'up':
            print('wait for file transfer')
            sftp.put(localpath, targetpath)
        if direction == 'down':
            print('wait for file transfer')
            sftp.get(targetpath, localpath)
        time.sleep(1)
        sftp.close()

    def pbc_comm_test(self):
        """performing this test will login to chassis-shell CLI"""
        self.pbc_console_login()
        if self.process_channel("chassis-shell\r").find("/>") == -1:
            return False
        else:
            return True

    def pbc_end_connection(self):
        self.ssh.close()

    def json_from_s(self, s):
        self.match = re.findall(r"{.+[:,].+}|\[.+[,:].+\]", s)
        return json.loads(self.match[0]) if self.match else None

    def process_channel(self, input):
        self.channel_data = str()
        self.host = str()
        self.scrfile = str()
        time.sleep(.5)
        self.channel.send(input)
        time.sleep(1.5)
        if self.channel.recv_ready():
            self.channel_data += str(self.channel.recv(9999).decode("utf8"))
        # print(self.channel_data)
        self._logger.info(self.channel_data)
        return self.channel_data

    # ######################### Communication Test ###########################

    def can_dump(self):
        self.process_channel("candump can0 | grep 7[0-9]\r")
        time.sleep(5)
        self.process_channel("\x03")

    # ######################### EMB Tests ###########################
    def pbc_console_login_old(self):
        self.process_channel('root\r')
        self.process_channel('root\r')

    def pbc_console_login(self):
        # self.process_channel('admin\r')
        # time.sleep(.5)
        # self.process_channel('config\r')
        # time.sleep(.5)
        self.process_channel('sudo -s\r')
        time.sleep(.5)
        if self.process_channel('config\r').find("root@") == -1:
            return False
        return True

    def pbc_console_exit(self):
        self.process_channel('\x03')  # send ctrl + c key
        self.process_channel('exit\r')

    def enter_chassis_shell(self):
        self.process_channel("chassis-shell\r")

    def exit_chassis_shell(self):
        self.process_channel('\x03')  # send ctrl + c key

    def return_chassis_shell_root(self):
        self.process_channel('/\r')  # send ctrl + c key

    def platform_sw_version(self):
        self.process_channel("/\r")
        self.process_channel("/Platform\r")
        self.process_channel("/PowerMonitor/board-rev\r")
        plat_read = self.process_channel("/Platform/EMB_PLATFORM_VERSION\r").split(" ")
        self._logger.info(f'UUT Platform version read: {plat_read[1]}')
        return plat_read[1]

    def init_all_can(self, evt: bool):  # Include the PM --no-detect bypass, must remove for DVT
        self.process_channel("CCB can0\r")
        self.process_channel("AUXPS can0\r")
        self.process_channel("/PM\r")
        if evt: self.pm_no_detect()
        for i in range(1, 6):
            self.process_channel('/PM/PM' + str(i) + ' can0\r')

    def init_all_pm(self):
        self.process_channel('/\r')
        self.process_channel('/PM\r')
        for i in range(1, 6):
            self.process_channel('PM' + str(i) + ' can0\r')

    def pm_init(self, pm):
        self.process_channel('/\r')
        self.process_channel('/PM\r')
        self.process_channel('PM' + str(pm) + ' can0\r')
        print(f'\nWating for PM{pm} to come online...')
        time.sleep(6)

    def get_temps(self):
        self.process_channel("/\r")
        self.process_channel("/TempSensor/TEMP1\r")
        self.process_channel("/CCB/temps\r")
        time.sleep(1)
        self.process_channel("/AUXPS/temps\r")
        time.sleep(1)
        self.process_channel("/PowerMonitor/temp 0\r")  # Powermonitor read DRY-Zone RTD temp read on C
        time.sleep(1)

    def toggle_all_pm(self):
        self.process_channel("/\r")
        for i in range(1, 6):
            self.process_channel('/PM/PM' + str(i) + ' op\r')
        time.sleep(.5)

    def show_pm_status(self, pm):
        self.process_channel("/\r")
        self.process_channel("/PM\r")
        self.process_channel("PM" + str(pm) + "\r")

    # ################### PBC LV Tests #########################
    def ext_chassis_led(self, r, g):
        if r == 1:
            self.process_channel("/ExtChassisLed/RED1 1\r")  # Set GREEN ON
        if r == 0:
            self.process_channel("/ExtChassisLed/RED1 0\r")  # Set GREEN ON
        if g == 1:
            self.process_channel("/ExtChassisLed/GREEN1 1\r")  # Set GREEN ON
        if g == 0:
            self.process_channel("/ExtChassisLed/GREEN1 0\r")  # Set GREEN ON

    def dry_zone_fan(self, fan, speed, enable):
        self.process_channel("/Fan/DRY-Zone-" + str(fan) + "\r")  # Enter PBC Fan directory
        self.process_channel("speed " + str(speed) + "\r")  # Set PBC Fan speed
        time.sleep(1.5)
        self.process_channel("power " + str(enable) + "\r")  # Set PBC Fan enable
        time.sleep(1.5)
        self.process_channel("\r")  # Status PBC Fan

    def dry_zone_one_fan_ctrl(self, fan, sp_else_pwr, enable):
        self.process_channel("/Fan/DRY-Zone-" + str(fan) + "\r")  # Enter PBC Fan directory
        if sp_else_pwr:
            sp = "100" if enable else "0"
            self.process_channel("speed " + str(sp) + "\r")  # Set PBC Fan speed
        time.sleep(.25)
        if not sp_else_pwr:
            self.process_channel("power " + str(enable) + "\r")  # Set PBC Fan enable
            time.sleep(.25)
        self.process_channel("\r")  # Status PBC Fan
        # time.sleep(.5)

    def dry_zone_fan_current(self, fan):  # DRY-Zone fan currents Powermonitor read DRY-Zone fan 1 and 2
        self.process_channel("/PowerMonitor/fan " + str(fan) + "\r")  # Powermonitor read DRY-Zone fan 1

    def gpio_expander(self):
        self.process_channel("/\r")
        self.process_channel("/GpioExpander\r")  # Read GpioExpander status

    def safety_sw(self, category):
        self.process_channel("/Reed\r")
        if category == 'thermal':
            self.process_channel("/ThermalSw\r")  # Read ThermalSw status
        if category == 'reed':
            self.process_channel("/Reed\r")
        if category == 'reed1':
            self.process_channel("REED1-DoorWetBoxFront\r")
        if category == 'surge':
            self.process_channel("/SurgeDet\r")

    # def pm_present_can_id():
    #     toggle_all_pm()
    #     show_pm_status()

    # CCB Tests
    def ccb_init(self):
        self.process_channel('\x03')  # send ctrl + c key
        self.enter_chassis_shell()
        self.process_channel("/CCB can0\r")
        time.sleep(1)
        # self.process_channel("/CCB op\r")

    def ccb_info(self):
        self.process_channel("/\r")
        self.process_channel("/CCB\r")

    def ccb_read_logs(self):  #
        self.process_channel(".quit\r")
        self.process_channel("cat /var/log/CCB-selftest.log\r")  # read dump

    def ccb_bl_fw_version(self):
        self.process_channel("/CCB/bootversion\r")
        self.process_channel("/CCB/appversion\r")

    def ccb_fault_info(self):
        self.process_channel("/CCB/faultInfo\r")

    def ccb_fan_bank_info(self, fanBank):
        if fanBank == 1:
            self.process_channel("/CCB/fanBank1\r")
        if fanBank == 2:
            self.process_channel("/CCB/fanBank2\r")
        if fanBank == 3:
            self.process_channel("/CCB/fanBank3\r")

    def ccb_pump_info(self):
        self.process_channel("/CCB/pump\r")

    def ccb_self_test(self):  # must run before trying to poll for CCB faults in ccb_fault_info()
        self.process_channel("/CCB/selfTest\r")

    def ccb_coolant_level(self):  # must run while filling up coolant tank
        self.process_channel("/CCB/coolantLevel\r")

    def ccb_fan_speed(self, b_num, f_speed):  # <bank_number> <speed 0-100> set fan-bank speed
        self.process_channel("/CCB/fanspeed " + str(b_num) + " " + str(f_speed) + "\r")  # Set CCB Fan speed
        time.sleep(1)

    def ccb_pump_speed(self, p_speed):  # <speed 0-100> set pump speed
        self.process_channel("/CCB/pumpspeed " + " " + str(p_speed) + "\r")  # Set CCB pump speed
        time.sleep(1)

    # Close Loop Thermal Control
    def autoThermal(self, poll, log_freq):  # <bank_number> <speed 0-100> set fan-bank speed
        self.process_channel("/PowerBlock/autoThermal  " + str(poll) + "\r")  # Set to close loop and poll freq
        time.sleep(1)
        self.process_channel("/PowerBlock/logInfo  " + str(log_freq) + "\r")  # Set to log freq in sec, default 5 sec
        time.sleep(1)

    # AUXPS Tests
    def auxps_info(self):
        # self.process_channel("/\r")
        self.process_channel("/AUXPS\r")

    def auxps_init(self):
        self.process_channel("/\r")
        self.process_channel("/AUXPS can0\r")

    def auxps_read_logs(self):  #
        self.process_channel(".quit\r")
        time.sleep(1)
        self.process_channel("cat /var/log/AuxPS-selftest.log\r")  # read dump

    def auxps_remove_logs(self):  #
        self.process_channel(".quit\r")
        time.sleep(1)
        self.process_channel("rm -v /var/log/AuxPS-selftest.log\r")  # read dump

    def auxps_bl_fw_version(self):
        self.process_channel("/AUXPS/bootversion\r")
        self.process_channel("/AUXPS/appversion\r")

    def auxps_bl_fw_version_test(self, check_bl_against: str):
        # Test BL/FW version
        self._logger.info('\n-->BL/App version test<--')
        self.bl_read = self.process_channel("/AUXPS/bootversion\r").split(" ")
        if self.bl_read[1].find(check_bl_against) != -1:
            self._logger.info(f'UUT PASSED Bootloader version test: {self.bl_read[1]}')
        else:
            self._logger.info(f'UUT FAILED current UUT BL version is: {self.bl_read[1]}')
            return False
        self.fw_read = self.process_channel("/AUXPS/appversion\r").split(" ")
        self._logger.info(f'UUT current Application version is: {self.fw_read[1]}')
        return True

    def auxps_fault_info(self):
        self.process_channel("/AUXPS/faults\r")

    def auxps_bank_info(self, auxBank):
        if auxBank == 'ccb':
            return self.json_from_s(self.process_channel("/AUXPS/CCBChannel\r"))
        if auxBank == 'pbc':
            return self.json_from_s(self.process_channel("/AUXPS/PBCChannel\r"))
        if auxBank == 'ext':
            return self.json_from_s(self.process_channel("/AUXPS/ExtChannel\r"))
        if auxBank == 'input':
            return self.json_from_s(self.process_channel("/AUXPS/InputChannel\r"))

    def auxps_channel_ctrl(self, ch: str, set_to: str):  # <ccb|pbc|ext> <0-3> 0:enable, 1:disable
        self.process_channel(f"/AUXPS/channelCtrl {ch} {set_to}\r")
        if ch == 'ccb':
            return self.json_from_s(self.process_channel("/AUXPS/CCBChannel\r"))
        if ch == 'pbc':
            return self.json_from_s(self.process_channel("/AUXPS/PBCChannel\r"))
        if ch == 'ext':
            return self.json_from_s(self.process_channel("/AUXPS/ExtChannel\r"))

    def auxps_self_test(self):  # must run before trying to poll for AUXPS faults in AUXPS_fault_info()
        self.process_channel("/AUXPS/selfTest\r")

    def auxps_shunt_ctrl(self, s_state):  #
        self.process_channel("/AUXPS/shuntControl " + str(s_state) + "\r")

    def auxps_fan_speed(self, af_speed):  # <speed 0-100> set fan speed
        return self.json_from_s(self.process_channel("/AUXPS/fanspeed " + str(af_speed) + "\r"))  # Set AUXPS Fan speed

    def auxps_fan_info(self):  # <speed 0-100>, <rpm>
        # self.response = self.process_channel("/AUXPS/fanstatus\r")  # SGet auxps Fan speed
        # time.sleep(1)
        # return self.json_from_s(self.response)
        return self.json_from_s(self.process_channel("/AUXPS/fanstatus\r"))  # SGet auxps Fan speed

    def auxps_autoPowerCycle(self, seconds):  # <seconds> Set auto power-cycle timeout on CAN/HB miss (current: 0sec)
        self.process_channel("/AUXPS/autoPowerCycle " + str(seconds) + "\r")  #
        time.sleep(1)

    def auxps_temps(self, humidity=False, dewpoint=False):
        # self.process_channel("/AUXPS/temps\r")  #
        # time.sleep(1)
        if humidity: self.process_channel("/AUXPS/humidity\r")  #
        if dewpoint: self.process_channel("/AUXPS/dewpoint\r")  #
        return self.json_from_s(self.process_channel("/AUXPS/temps\r"))

    def auxps_input_channel_info(self):  # show all 3x input channels
        return self.json_from_s(self.process_channel("/AUXPS/InputChannel\r"))

    # PM Power Control
    def pm_no_detect(self):  #
        self.process_channel("/\r")
        self.process_channel("/PM\r")
        self.process_channel("--no-detect\r")  # set PBC to no MPx GPIO pin detect
        time.sleep(1)

    def pm_bl_fw_version(self, pm):
        self.process_channel("/PM/PM" + str(pm) + "/bootversion\r")
        self.process_channel("/PM/PM" + str(pm) + "/appversion\r")

    # def pm_pwr_ctrl(self, pm, bus, volts, amps):  # <a|b|0> <volts> <amps> [maxvolts]    Set pm output bus/volts/amps
    #     self.process_channel("/PM/PM" + str(pm) + "/setTargets " + str(bus) + " " + str(volts) + " " + str(amps) + "\r")
    #     time.sleep(1)

    def pm_pwr_ctrl(self, pm, bus, volts, amps):  # <a|b|0> <volts> <amps> [maxvolts]    Set pm output bus/volts/amps
        self.process_channel("/\r")
        self.process_channel(f"/PM/PM{pm}\r")
        # self.process_channel("/PM/PM" + str(pm) + " \r")
        self.process_channel(f"setTargets {bus} {volts} {amps}\r")
        time.sleep(2)
        self.process_channel("\r")
        self.process_channel("/\r")

    #### BK Test
    def bk_pwr_ctrl(self, state):
        # self._res_manager.write(b"OUTPut ON\r\n")
        if state == 1:
            self.process_channel("OUTPut ON\n")
        if state == 0:
            self.process_channel("OUTPut OFF\n")
        time.sleep(1)

    # Burn-in test
    def pb_bi_test(self, bus: str, volts: str, amps: str, pm1_5: bool):
        if pm1_5:
            power_kw = '200'  # set 200kW max power if PM 1.5
        else:
            power_kw = '156'
        self.pbc_console_login()
        self.enable_ssh()
        time.sleep(1)
        self.process_channel(f"test-pnode -r {bus} {power_kw}\r")  #
        time.sleep(1)
        self.process_channel(f"test-pnode {bus} {volts} {amps}\r")  # < a | b > < powerkw >
        time.sleep(1)


def main():

    logging.basicConfig(level=logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger()
    logger.addHandler(stdout_handler)

    _pbc_ser = PBC_Ser('COM18')
    _pbc_ser.enable_ssh_2()
    _pbc_ser.close()
    _pbc_ssh = PBC_SSH('fe80::ffd2:8387:281b:1074')
    _pbc_ssh.pbc_console_login()
    _pbc_ssh.enter_chassis_shell()
    _pbc_ssh.safety_sw('reed1')

    _pbc_ssh.pbc_end_connection()


if __name__ == "__main__": main()
