# -*- coding: utf-8 -*-
"""
Name: Exchange_OPCUA_Servers.py
This script exchange values between different OPC UA Servers based on the
configuration stored on the file opcua_exchange_conf.xml
@author: Jesús M. Zamarreño

Copyright (C) 2023  Jesús M. Zamarreño

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# %%
# Library for XML import
import xml.etree.ElementTree as ET

# Libreries OPC UA
from opcua import Client
from opcua import ua

# Others
import time as Time

# %%
# Read and parse configuration file

tree = ET.parse('opcua_exchange_conf.xml')  # reading configuration file
root = tree.getroot()

exT = float(root.attrib['exchange_time'])  # exchange time period in seconds

ServerNames = []  # List of strings with Server Names
ServerURLs = []  # List of strings with Server URLs
# Searching OPC UA Servers on the XML configuration file
for servers in root.iter('OPCServer'):
    ServerNames.append(servers.attrib['name'])
    ServerURLs.append(servers.attrib['url'])

VariableSources = []  # List for variable sources as a tuple: server number, tag
VariableTargets = []  # List for variable targets as a tuple: server, tag
Types = []            # List for variable types; useful when writing values

for child in root:
    if child.tag == 'OPCLinks':  # Searching for variables for exchange section
        print(child.tag)
        for child2 in child:
            print(child2.tag)
            if child2.tag == 'OPCLink_vars':  # Exchange information
                # Server number acting as source
                i = ServerNames.index(child2.attrib['source'])
                # Server number acting as target
                j = ServerNames.index(child2.attrib['target'])
                # Variables for exchange
                for variable in child2.findall('variable'):
                    # Server number and variable to read
                    VariableSources.append((i, variable.get('source')))
                    # Server number and variable to write
                    VariableTargets.append((j, variable.get('target')))
                    Types.append(variable.get('type'))  # Type for writing

# %%

# Connecting to the OPC UA servers
# If second argument: read/write request timeout

# Connect to Servers
SS = []  # List of servers objects connections
for url in ServerURLs:
    SS.append(Client(url))

for ss, nn in zip(SS, ServerNames):
    while True:
        try:
            ss.connect()  # Trying to connect to every server
        except (ConnectionRefusedError) as error:
            print(f'Se ha producido el error: \'{error}\'.')
        else:
            print(f'Conexión establecida con {nn}')
            break

# %%
# Variables for reading
readlist = []  # List of node objects
for v in VariableSources:  # Recover server numbers and variable tags
    i, tag = v
    s = SS[i]  # Server object
    readlist.append(s.get_node(tag))  # Append node to be read

# %%
# Variables for writing
writelist = []  # List of node objects
typelist = []   # List of types
for v, t in zip(VariableTargets, Types):  # Recover server numbers and variable tags
    i, tag = v
    s = SS[i]  # Server object
    writelist.append(s.get_node(tag))  # Append node to be written
    eval(f'typelist.append(ua.VariantType.{t})')  # Data type for writting

# %%

# Exchange loop
try:
    while True:

        start = Time.time()  # For calculating elapsed time

        # Read from readlist and Write to writelist
        for r, w, t, n1, n2 in zip(readlist, writelist, typelist, VariableSources, VariableTargets):
            read_value = r.get_value()  # Read value
            w.set_value(ua.DataValue(ua.Variant(read_value, t)))  # Write value
            s1, tag1 = n1  # Server number and tag for console information
            s2, tag2 = n2
            print(f'{ServerNames[s1]}::{tag1}: {read_value} --> {ServerNames[s2]}::{tag2}')

        end = Time.time()  # For calculating elapsed time
        t_calculo = end - start  # elapsed time in seconds

        if t_calculo > 0:  # Avoid division by zero
            factor = exT/t_calculo  # Ratio
        else:
            factor = 1000

        if factor > 1:  # exchange time has been faster than elapsed time
            Time.sleep(exT - t_calculo)  # for real-time exchange
            print("exT: " + str(exT) +
                  " - Calculation time: " + str(t_calculo))
        else:
            print("Warning: Calculation time longer than real-time")

except KeyboardInterrupt:
    pass

# Disconnect from servers
for s in SS:
    s.disconnect()
