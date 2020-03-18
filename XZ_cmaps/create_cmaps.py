import numpy as np
import proplot as plot
from matplotlib.colors import LinearSegmentedColormap

# dbz
colors = ["#CCCCCC", "#00CCFF", "#0066FF", "#0033CC", "#00FF66",
          "#33CC66", "#009900", "#FFFF66", "#FFCC33", "#FF9900",
          "#FF6666", "#FF3333", "#CC0000", "#FF00FF", "#CD00CD",
          "#800080"]

cmap_name = 'dbz'
n_bins = np.arange(-5, 80, 5)
cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=16)
plot.Colormap(cm, save=True, name=cmap_name)