# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 07:53:16 2023

@author: noo029
"""

import os
import sys
from tempfile import TemporaryDirectory

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import flopy


print(sys.version)
print("numpy version: {}".format(np.__version__))
print("matplotlib version: {}".format(mpl.__version__))
print("flopy version: {}".format(flopy.__version__))

# For this example, we will set up a temporary workspace.
# Model input files and output files will reside here.
temp_dir = TemporaryDirectory()
workspace = os.path.join(temp_dir.name, "mf6Well")

workspace = os.path.join(".", "mf6Well")
try: 
    os.mkdir(workspace) 
    print("Directory '%s' created" %workspace) 
except OSError as error: 
    print(error)    

#%%
model_name = "well_00"
initial_head = 0 # meters
const_head = 0 # meters
nlay, nrow, ncol = 1, 15, 15 
L = 15000 # meters
H = 100. # meters
hk = 1.0 # m/d
#%% Flopy simulation object
# Create the Flopy simulation object
sim = flopy.mf6.MFSimulation(
    sim_name=model_name, 
    exe_name=os.path.join("bin","mf6.exe"), 
    version="mf6", sim_ws=workspace
)
#%% Flopy temporal discretization object
# Create the Flopy temporal discretization object
ntinesteps = 19
tdis = flopy.mf6.ModflowTdis(
    sim, pname="tdis", time_units="DAYS", nper=1, 
    perioddata=[(3650, ntinesteps, 1.5)],
)
#%% Flopy groundwater flow (gwf) model object
# Create the Flopy groundwater flow (gwf) model object
gwf_name = "gwf_well_00"
model_nam_file = "{}.nam".format(gwf_name)
gwf = flopy.mf6.ModflowGwf(sim, 
    modelname="gwf_well_00", 
    model_nam_file=model_nam_file)
#%% Flopy iterative model solver (ims) Package object
# Create the Flopy iterative model solver (ims) Package object
ims = flopy.mf6.ModflowIms(sim, 
    pname="ims", 
    complexity="SIMPLE")
#%% Flopy discretization (dis) Package object
# Create the Flopy discretization (dis) Package object
bot = -100
delrow = delcol = 1000.
dis = flopy.mf6.ModflowGwfdis(
    gwf,
    pname="dis",
    nlay=nlay,
    nrow=nrow,
    ncol=ncol,
    delr=delrow,
    delc=delcol,
    top=0.0,
    botm=bot,
)
#%% Flopy initial conditions (ic) Package object
# Create the Flopy initial conditions (ic) Package object
start = initial_head
ic = flopy.mf6.modflow.mfgwfic.ModflowGwfic(gwf, 
    pname="ic", 
    strt=start)
#%% Flopy node property (npf) Package object
# Create the Flopy node property (npf) Package object
npf = flopy.mf6.modflow.mfgwfnpf.ModflowGwfnpf(
    gwf, 
    pname="npf", 
    icelltype=1, 
    k=hk, 
    save_flows=True
)
#%% Flopy storage (sto) Package object
# Create the Flopy storage (sto) Package object
sto = flopy.mf6.ModflowGwfsto(
    gwf,
    pname="sto",
    save_flows=True,
    iconvert=[0],
    ss=2.0e-6,
    sy=0.2,
    transient={0: True},
) 

#%% Flopy storage (sto) Package object
# Create the Flopy well (wel) Package object
tdis.nper
stress_period_data = {}
for p in range(tdis.nper.array):
    stress_period_data[p] = [0, 7, 7,-600.,'well_00']

wel = flopy.mf6.ModflowGwfwel(
    gwf,
    pname="wel",
    print_input=True,
    print_flows=True,
    #auxiliary=[("var1")],
    maxbound=19,
    stress_period_data=stress_period_data,
    boundnames=True,
    save_flows=True,
)

ra_wel = wel.stress_period_data.get_data(key=0)

#%% Flopy constant head (chd) Package object
# Create the Flopy constant head (chd) Package object
# List information is created a bit differently for
# MODFLOW 6 than for other MODFLOW versions.  The
# cellid (layer, row, column, for a regular grid)
# must be entered as a tuple as the first entry.
# Remember that these must be zero-based indices!
chd_rec = []
for col in range(0, ncol):
    chd_rec.append([0, 0, col, const_head])

chd = flopy.mf6.ModflowGwfchd(
    gwf,
    pname="chd",
    maxbound=len(chd_rec),
    stress_period_data={0: chd_rec},
    save_flows=True,
)

# The chd package stored the constant heads in a structured
# array, also called a recarray.  We can get a pointer to the
# recarray for the first stress period (iper = 0) as follows.
iper = 0
ra = chd.stress_period_data.get_data(key=0)
print(ra.head)
#%% Plot boundary conditions
# We can make a quick plot to show where our constant
# heads are located by creating an integer array
# that starts with ones everywhere, but is assigned
# a -1 where chds are located
ibd = np.ones((nlay, nrow, ncol), dtype=int)
for k, i, j in ra["cellid"]:
    ibd[k, i, j] = -1

for k, i, j in ra_wel["cellid"]:
    ibd[k, i, j] = 0
    
plt.imshow(ibd[0, :, :], interpolation="none")
plt.title("Layer {}: Constant Head Cells".format(1))

#%% Flopy output control (oc) Package object
# Create the Flopy output control (oc) Package object
headfile = "{}.hds".format(gwf_name)
head_filerecord = [headfile]
budgetfile = "{}.cbb".format(gwf_name)
budget_filerecord = [budgetfile]
# Note mf6 no longer supports drawdown output 
saverecord = [("HEAD", "ALL"), ("BUDGET", "ALL")]
printrecord = [("HEAD", "LAST")]
oc = flopy.mf6.ModflowGwfoc(
    gwf,
    pname="oc",
    saverecord=saverecord,
    head_filerecord=head_filerecord,
    budget_filerecord=budget_filerecord,
    printrecord=printrecord,
)

# Note that help can always be found for a package
# using either forms of the following syntax
help(oc)
# help(flopy.mf6.modflow.mfgwfoc.ModflowGwfoc)

#%% Write the datasets
# Write the datasets
sim.write_simulation()
gwf.write()

# Run the simulation
success, buff = sim.run_simulation(silent=True, report=True)
if success:
    for line in buff:
        print(line)
else:
    raise ValueError("Failed to run.")
