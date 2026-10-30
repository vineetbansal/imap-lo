import os
import numpy as np
import pandas as pd

# Constants and Parameters
#MAPS_DIR = '../maps'
#COSALPHA_DIR = 'cosalpha'
#OUT_DIR = 'maps_cg_corrected'

BKG_CONST = 0.0  # Constant background value to subtract if strictly necessary (default 0)

# SC Energy of neutral H (approx 30 km/s spacecraft speed produces ~4.66 eV)
E_u = 4.661

# Nominal IMAP-Lo energy geometric geometric centers (eV)
E_k = np.array([16.0, 30.0, 56.0, 106.0, 200.0, 404.0, 787.0], dtype=float)

# Transmission scale factor polynomial coefficients M0...M5 from Table 1
M_eta = np.array([
    [1.01052, -0.047723, 0.030400, -0.0018170, 0.0023649, -0.00032519],
    [1.01420, -0.045778, 0.030061, -0.0020424, 0.0021796, -0.00029036],
    [1.01300, -0.045334, 0.030649, -0.0021426, 0.0021755, -0.00028690],
    [1.01090, -0.043671, 0.029741, -0.0014197, 0.0016756, -0.00022980],
    [1.01450, -0.045219, 0.029705, -0.0021726, 0.0020739, -0.00026520],
    [1.01160, -0.043433, 0.030755, -0.0020747, 0.0018990, -0.00024760],
    [1.01560, -0.048728, 0.029868, -0.0016762, 0.0022885, -0.00031830]
])

def load_maps(work_dir_sputterboot, work_dir_cosalpha):
    """Loads flux, func (uncertainty), and fvar (variance) from CSV maps across 7 energy levels."""
    print(f"Loading files from {work_dir_sputterboot}...")
    flux = np.zeros((30, 60, 7))
    func = np.zeros((30, 60, 7))
    # this includes only the systematic uncertainty
    fvar = np.zeros((30, 60, 7))
    # here the variance is the random uncertaint
    cosalpha = np.zeros((30, 60, 7))

    for k in range(7):
        esa = k + 1
        # Read maps, skip column names if present, but typically the first row/column contain coordinates/indices.
        # Based on inspection, row 1 is x-index, and data is 31 rows by 60 columns.
        f_df = pd.read_csv(f'{work_dir_sputterboot}/map_flux_{esa}_Hy_boot_cor.csv', skiprows=1, header=None)
        u_df = pd.read_csv(f'{work_dir_sputterboot}/map_flux_{esa}_Hy_boot_unc.csv', skiprows=1, header=None)
        v_df = pd.read_csv(f'{work_dir_sputterboot}/map_flux_{esa}_Hy_boot_var.csv', skiprows=1, header=None)
        w_df = pd.read_csv(f'{work_dir_cosalpha}/map_cosalpha_esa{esa}.csv', skiprows=1, header=None)    

        flux[:, :, k] = f_df.values[:, :]
        func[:, :, k] = u_df.values[:, :]
        fvar[:, :, k] = v_df.values[:, :]
        cosalpha[:,:,k] = w_df.values[:,:]

    print(f"Completed loading grid shape: {flux[:,:,0].shape}")
    return flux, func, fvar, cosalpha

def compute_kinematics(cosalpha_map):
    """Calculate Eh_k and Es_k from cosalpha_map, fixed E_k, and E_u."""

    cos_alpha = np.clip(cosalpha_map, -1.0, 1.0)
    sin_alpha = np.sqrt(np.maximum(0.0, 1.0 - cos_alpha**2))

    nlat, nlon, nesa = cos_alpha.shape

    Es_k = np.zeros((nlat, nlon, nesa))
    Eh_k = np.zeros((nlat, nlon, nesa))

    for k in range(nesa):

        Eh_k[:, :, k] = E_k[k]

        yk = np.sqrt(E_k[k] / E_u)

        term = yk**2 - sin_alpha[:, :, k]**2
        term = np.maximum(term, 0.0)

        xk = cos_alpha[:, :, k] + np.sqrt(term)

        Es_k[:, :, k] = xk**2 * E_u
        # projected s/c frame energy

    return Es_k, Eh_k, cos_alpha

def predictor_corrector(flux, max_iter=20, tol=0.005):
    """
    Computes final power-law (gamma) and true source flux (J_src) by 
    iteratively resolving instrument transmission bias (eta).
    """
    J = np.copy(flux) - BKG_CONST
    J[J <= 0] = np.nan # Nullify non-positive for log space

    N_lat, N_lon, N_e = J.shape
    Jf = J.reshape(-1, N_e)
    
    def get_gamma(J_arr):
        g = np.zeros_like(J_arr)
        with np.errstate(divide='ignore', invalid='ignore'):
            for k in range(N_e - 1):
                g[:, k] = np.log(J_arr[:, k+1] / J_arr[:, k]) / np.log(E_k[k+1] / E_k[k])
        g[:, N_e-1] = g[:, N_e-2]
        return g

    def get_eta(g_arr):
        e = np.zeros_like(g_arr)
        for k in range(N_e):
            gv = g_arr[:, k]
            e[:, k] = (M_eta[k,0] + M_eta[k,1]*gv + M_eta[k,2]*(gv**2) + 
                       M_eta[k,3]*(gv**3) + M_eta[k,4]*(gv**4) + M_eta[k,5]*(gv**5))
        return e

    # Step 1: Initial predictors
    g0 = get_gamma(Jf)
    eta = get_eta(g0)
    Jsrc = Jf / eta

    # Iteration
    for i in range(max_iter):
        g_pred = get_gamma(Jsrc)
        g_half = 0.5 * (g0 + g_pred)
        eta_h = get_eta(g_half)
        J_half = Jf / eta_h

        g_corr = get_gamma(J_half)
        g_new = 0.5 * (g0 + g_corr)  # Appendix A: gamma_n=1 = (1/2)*(gamma_n=0 + gamma_n=0.5,c)
        eta_new = get_eta(g_new)
        J_new = Jf / eta_new

        with np.errstate(divide='ignore', invalid='ignore'):
            chi = np.nanmean((J_new / Jsrc)**2)**0.5 - 1.0

        Jsrc = J_new
        g0 = g_new
        
        if not np.isnan(chi) and abs(chi) < tol:
            print(f"Convergence reached at iteration {i+1} (chi: {chi:.5f})")
            break
            
    return Jsrc.reshape(N_lat, N_lon, N_e), g0.reshape(N_lat, N_lon, N_e)

def apply_compton_getting():

    for pp in [75,90,105]:

        work_dir=f'../3S7_l1b_sputterbootstrap_ram/outdir/pivot_{pp}/maps/'
        work_dir_cosalpha=f'../3S5_l1b_ram_maps/outdir/pivot_{pp}/maps/'
        out_dir=f'./outdir/pivot_{pp}/maps/'

        os.makedirs(out_dir,exist_ok=True)

        flux, func, fvar, cosalpha = load_maps(work_dir, work_dir_cosalpha)

        Es_k, Eh_k, cos_alpha = compute_kinematics(cosalpha)
    
        print("Computing source fluxes and power-laws... pivot", pp)
        J_src, gamma = predictor_corrector(flux)
    
        print("Applying Compton-Getting scale factoring... pivot", pp)
        J_cg = np.zeros_like(flux)
        func_cg = np.zeros_like(func)
        fvar_cg = np.zeros_like(fvar)
    
        for k in range(7):
            # Scale Flux
            factor = (Es_k[:, :, k] / E_k[k])**(gamma[:, :, k] + 1.0)
            J_cg[:, :, k] = J_src[:, :, k] * factor
        
        # Propagate Uncertainties 
        # Fractional uncertainties remain largely invariant in linear approximation, 
        # although formal document states multiplying by factor. 
        # Here we scale absolute uncertainty proportionally.
            ratio = J_cg[:, :, k] / flux[:, :, k]
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = J_cg[:, :, k] / flux[:, :, k]   
            ratio[~np.isfinite(ratio)] = np.nan

            func_cg[:, :, k] = func[:, :, k] * ratio
            fvar_cg[:, :, k] = fvar[:, :, k] * (ratio**2)
        
        print("Saving to CSV... pivot ", pp)
        # Generate Output 
        cols_idx = np.arange(60).astype(str)
        for k in range(7):
            esa = k + 1
        # Save Flux
            df_j = pd.DataFrame(np.nan_to_num(J_cg[:, :, k], nan=0.0))
            df_j.columns = cols_idx
            df_j.to_csv(f'{out_dir}/map_cgflux_esa{esa}.csv', index=False)
        
        # Save Func
            df_u = pd.DataFrame(np.nan_to_num(func_cg[:, :, k], nan=0.0))
            df_u.columns = cols_idx
            df_u.to_csv(f'{out_dir}/map_cgfunc_esa{esa}.csv', index=False)
        
        # Save Fvar
            df_v = pd.DataFrame(np.nan_to_num(fvar_cg[:, :, k], nan=0.0))
            df_v.columns = cols_idx
            df_v.to_csv(f'{out_dir}/map_cgfvar_esa{esa}.csv', index=False)
        
        print("Compton-Getting correction completed successfully! pivot ", pp)

if __name__ == '__main__':
    apply_compton_getting()
