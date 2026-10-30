import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

trustee = {
    "20": [124, 127, 123, 134, 123, 130, 120, 118, 122, 119],
    "50": [305, 278, 362, 308, 297, 303, 328, 277, 285, 344],
}

pepper = {
    "20": [128, 125, 134, 115, 119, 127, 116, 126, 136, 192],
    "50": [318, 260, 298, 246, 278, 266, 259, 282, 339, 296],
}

times_faster2 = {}
for key in trustee:
    avg_method_1 = sum(trustee[key]) / len(trustee[key])
    print("Avg for TRUSTEE", key, avg_method_1)
    avg_PEPPER = sum(pepper[key]) / len(pepper[key])
    print("Avg for PEPPER", key, avg_method_1)
    ratio = avg_method_1 / avg_PEPPER
    times_faster2[key] = ratio
print(times_faster2)

# Waiting time data for each category and process
waiting_time_data = {
    "2000": [12.37, 14.77, 17.60, 15.54, 31, 15.5, 16.2, 17.4, 14, 28.8],
    "3000": [31.916, 22.15, 19.8, 32.13, 28.13, 32.5, 30.02, 32.24, 32.811, 38.41],
    "4000": [34.46, 59.21, 65.5, 64.8, 43.1, 65, 40.6, 144, 41, 70],
    "5000": [64, 77.8, 137, 138, 127, 142, 51, 133, 139, 240],
    "6000": [68, 133, 72, 154, 68, 132, 267, 136, 74, 148],
}

tatal_time_for_PEPPER = {
    "2000": [9.79, 15, 11, 10.5, 15, 11, 10, 10.7, 11, 10.7],
    "3000": [17.6, 17.7, 18.6, 17.5, 19, 18.7, 24, 19.5, 20, 20],
    "4000": [22.5, 33.5, 35, 41.5, 25, 26, 26.5, 28, 27.1, 27],
    "5000": [65.6, 126, 37, 65, 40, 84, 63, 72, 31.7, 47],
    # "6000": [32.3, 65, 147, 131.6, 149, 74.4, 70.5, 78.6, 135, 132]
    "6000": [31.6, 65, 131, 33.7, 140, 135, 146, 66, 146, 138],
}

times_faster = {}
for key in waiting_time_data:
    avg_method_1 = sum(waiting_time_data[key]) / len(waiting_time_data[key])
    avg_PEPPER = sum(tatal_time_for_PEPPER[key]) / len(tatal_time_for_PEPPER[key])
    ratio = avg_method_1 / avg_PEPPER
    times_faster[key] = ratio

print(times_faster)

process_labels = list(waiting_time_data.keys())
process_data_device1 = list(tatal_time_for_PEPPER.values())
process_data_device2 = list(waiting_time_data.values())

# Combine the data for both devices
combined_data = [
    data for pair in zip(process_data_device1, process_data_device2) for data in pair
]


# Create labels and positions for the grouped box plot
positions = [
    2 * i + offset for i in range(len(process_labels)) for offset in [0, 0.55]
]  # Using 0 and 1 as offsets
fig, ax = plt.subplots(figsize=(8, 6.4))

# Create the grouped box plot
boxplot = ax.boxplot(combined_data, positions=positions, patch_artist=True)

for median in boxplot["medians"]:
    median.set(color="black")

# Set colors using hexadecimal color codes
colors = ["#5975A4" if i % 2 == 0 else "#5F9E6E" for i in range(len(boxplot["boxes"]))]
for patch, color in zip(boxplot["boxes"], colors):
    patch.set_facecolor(color)


# Set custom tick positions for better alignment with grouped boxes
tick_positions = [
    (positions[i] + positions[i + 1]) / 2 for i in range(0, len(positions), 2)
]
plt.xticks(ticks=tick_positions, labels=process_labels, fontsize=16)
plt.yticks(fontsize=16)

# ax.set_title('Comparison between Trustee[17] and PEPPER')
ax.set_xlabel("Number of bidders", fontsize=18)
ax.set_ylabel("Remote Attestation Elapsed Time (s)", fontsize=16.5)

ax.yaxis.grid(True)
ax.set_ylim(0, 170)

# Create legend patches using hexadecimal color codes
trustee_patch = mpatches.Patch(color="#5975A4", label="PEPPER")
pepper_patch = mpatches.Patch(color="#5F9E6E", label="Trustee [17]")

# Add legend to the plot
plt.legend(handles=[trustee_patch, pepper_patch], loc="upper left", fontsize="14")

plt.tight_layout()
plt.savefig("/Users/emrahsariboz/Downloads/data-updated.pdf", bbox_inches="tight")
plt.show()
