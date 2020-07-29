from meshoid import Meshoid
from load_from_snapshot import load_from_snapshot
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import colors

# physical constants
boltzmann_cgs = 1.380658e-16 # erg K^{-1}
m_H = 1.6733e-24    # g
gamma = 5./3.   # assumed constant

# conversion factor from specific energy in code units to specific energy in cgs
unittime_cgs = 3.08568e16    # s  (0.976 Gyr in s)
unitlength_cgs = 3.085678e21 # cm (1 kpc in cm)
unitmass_cgs = 1.989e43      # g  (1e10 Msun in g)
unitenergypermass_cgs = unitlength_cgs**(2) * unittime_cgs**(-2) # erg g^{-1}
unitdensity_cgs = unitmass_cgs * unitlength_cgs**(-3) # g cm^{-3}
unitdensity_per_H = unitdensity_cgs / m_H

def load_hydro_data(filename):
    pdata = {}
    for field in "Masses", "Coordinates", "SmoothingLength", "Velocities", "InternalEnergy", "ElectronAbundance":
        pdata[field] = load_from_snapshot(field, 0, filename)
    return pdata

def compute_temperature(pdata):
    # *only* if COOL_LINE_METALS is enabled
    #N_species = 10
    #MetallicityMask = np.ones(1+N_species)
    #pdata["Metallicity"] = load_from_snapshot("Metallicity", 0, "output/", snap_num, axis_mask=MetallicityMask)
    #y_Helium = pdata["Metallicity"][:,1]

    x_H = 0.75
    y_Helium = 0.23
    z_metals = 0.02
    H_term = x_H
    He_term = y_Helium/4.0
    z_term = z_metals/2.0   # this term is ignored
    e_term = x_H + y_Helium*(2)/4.0
    mu_fullyionized = 1.0 / (H_term + He_term + e_term)

    #print(f"fully-ionized mean molecular weight (dimensionless): {mu_fullyionized}")
    #print(f"maximium electron abundance: {np.max(pdata['ElectronAbundance'])}")

    InternalEnergy = pdata["InternalEnergy"] * unitenergypermass_cgs
    e_term = pdata["ElectronAbundance"]
    mu = 1.0 / (H_term + He_term + e_term)

    mean_molecular_weight = mu * m_H
    T = (mean_molecular_weight / boltzmann_cgs) * (gamma-1) * InternalEnergy
    return T

def apply_radius_cut(pdata, T):
    pos = pdata["Coordinates"]
    center = np.median(pos,axis=0)
    pos -= center
    radius_max = 40.0 # kpc
    radius_cut = np.sum(pos*pos,axis=1) < (radius_max**2)
    pos, mass, hsml, v = pos[radius_cut], pdata['Masses'][radius_cut], pdata['SmoothingLength'][radius_cut], pdata['Velocities'][radius_cut]
    temp = T[radius_cut]
    return pos, mass, hsml, v, temp

def save_phase_plot(input_dens, temp, filename):
    ## make phase plot! (temperature vs n_H)
    dens = input_dens * unitdensity_per_H
    print(f"density = {dens}")
    lognHmin = -6.0
    lognHmax = 3.0
    logTmin = 1.0
    logTmax = 8.0
    h = plt.hist2d(np.log10(dens), np.log10(temp),
                    bins=100, norm=colors.LogNorm(),
                    range = [[lognHmin,lognHmax], [logTmin,logTmax]])
    plt.colorbar(label=r'proportional to mass') # unclear what units of this are
    plt.xlabel(r'$\log_{10}$ density ($n_{H}$ [cm$^{-3}$])')
    plt.ylabel(r'$\log_{10}$ temperature (K)')
    plt.tight_layout()
    plt.savefig(filename)
    plt.clf()

def save_slice_plot(mesh, field, filename, colorbar_label=""):
    rmax = 20
    res = 1000
    x = y = np.linspace(-rmax,rmax,res)
    X, Y = np.meshgrid(x, y)

    #sigma_gas_msun_pc2 = 1e4 * M.SurfaceDensity(M.m,center=np.array([0,0,0]),size=40.,res=res)
    #density_slice_nHcgs =300 * M.Slice(M.Density(),center=np.array([0,0,0]),size=40.,res=res)
    slice = mesh.Slice(field,center=np.array([0,0,0]),size=40.,res=res)

    fig,ax = plt.subplots(figsize=(6,6))
    p = ax.imshow(slice, cmap='viridis',
                    extent=[x.min(), x.max(), y.min(), y.max()],
                    interpolation='nearest',
                    origin='lower',
                    aspect='equal',
                    norm=colors.LogNorm())

    ax.set_aspect('equal')
    #fig.colorbar(p,label=r"$\Sigma_{gas}$ $(\rm M_\odot\,pc^{-2})$")
    #fig.colorbar(p, label=r"$n_{H}$ (cm$^{-3}$)")
    fig.colorbar(p, label=colorbar_label)
    ax.set_xlabel("X (kpc)")
    ax.set_ylabel("Y (kpc)")
    plt.savefig(filename)

def save_density_projection_plot(mesh, filename,
                                colorbar_label=r"$\Sigma_{gas}$ $(\rm M_\odot\,pc^{-2})$"):
    rmax = 20
    res = 1000
    x = y = np.linspace(-rmax,rmax,res)
    X, Y = np.meshgrid(x, y)

    sigma_gas_msun_pc2 = 1e4 * mesh.SurfaceDensity(mesh.m,
                                    center=np.array([0,0,0]),size=40.,res=res)

    fig,ax = plt.subplots(figsize=(6,6))
    p = ax.imshow(sigma_gas_msun_pc2, cmap='viridis',
                    extent=[x.min(), x.max(), y.min(), y.max()],
                    interpolation='nearest',
                    origin='lower',
                    aspect='equal',
                    norm=colors.LogNorm())

    ax.set_aspect('equal')
    fig.colorbar(p, label=colorbar_label)
    ax.set_xlabel("X (kpc)")
    ax.set_ylabel("Y (kpc)")
    plt.savefig(filename)

def compute_mesh(pdata):
    return Meshoid(pdata["Coordinates"], pdata["Masses"], pdata["SmoothingLength"])