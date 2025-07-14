import numpy as np, matplotlib.pyplot as plt

# ---------- parameters ----------
N        = 65536                # lots of points → smooth FFT
opd_max  = 0.4                  # ±0.4 cm travel
t        = np.linspace(-opd_max, opd_max, N)
dt       = t[1] - t[0]

# two Lorentzian lines at 60 cm⁻¹ (narrow) and 100 cm⁻¹ (broad)
def lorentz(nu0, fwhm, amp=1):
    gamma = fwhm/2
    return amp * gamma**2 / ((freq - nu0)**2 + gamma**2)

# spectrum grid (for plotting ground truth)
freq = np.fft.fftfreq(N, d=dt)
pos  = freq >= 0
spectrum = lorentz(60, 2) + lorentz(100, 6)

# build corresponding interferogram via inverse FFT
fft_array       = np.zeros_like(freq, dtype=complex)
fft_array[pos]  = spectrum[pos]          # positive half
fft_array[~pos] = spectrum[pos][::-1]    # enforce Hermitian symmetry
interferogram   = np.fft.ifft(fft_array).real

# add realistic centre-burst scaling and a touch of noise
interferogram *= 1e3                     # make the centre-burst huge
interferogram += 0.02 * interferogram.max() * np.random.randn(N)

# ---------- plotting ----------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

ax1.plot(t, interferogram, lw=0.7)
ax1.set_xlabel('Time / Optical-Path Difference (cm)')
ax1.set_ylabel('Intensity (a.u.)')
ax1.set_title('Interferogram')
ax1.set_xlim(-opd_max, opd_max)

ax2.plot(freq[pos], spectrum[pos], lw=0.7)
ax2.set_xlabel('Wavenumber (cm$^{-1}$)')
ax2.set_ylabel('Intensity (a.u.)')
ax2.set_title('Spectrum')
ax2.set_xlim(0, 120)

for ax in (ax1, ax2):
    ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.show()



