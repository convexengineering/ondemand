from stol import Mission
import matplotlib.pyplot as plt
import numpy as np
import sys
from gpkit.repr_conventions import unitstr

#pylint: disable=invalid-name, anomalous-backslash-in-string

def plot_sens(model, result, varnames=None):
    fig, ax = plt.subplots()
    pss = []
    ngs = []
    sens = {}
    if varnames:
        for vname in varnames:
            sen = result["sensitivities"]["constants"][vname]
            if hasattr(sen, "__len__"):
                val = max(np.abs(sen.values()))
                vk = [svk for svk in sen if abs(sen[svk]) == val][0]
                # sen = result["sensitivities"]["constants"][vk]
                sen = sum(sen.values())
            else:
                vk = model[vname].key
            sens[vk] = sen
    else:
        for s in result["sensitivities"]["constants"]:
            sens[s] = sum(np.hstack([result["sensitivities"]["constants"][s]]))

    labels = []
    i = 0
    sorted_sens = sorted(sens.items(), key=lambda x: np.absolute(x[1]),
                         reverse=True)

    for s in sorted_sens:
        i += 1
        if i > 15:
            break
        if hasattr(model[s[0]], "__len__"):
            vk = model[s[0]][0]
        else:
            vk = s[0]
        val = sum(np.hstack([model.substitutions[vk]]))
        if "units" in vk.descr:
            uts = unitstr(vk.descr["units"])
        else:
            uts = "-"

        labels.append(vk.descr["label"] + " =%.2f [%s]" % (val, uts))
        if s[1] > 0:
            pss.append(s[1])
            ngs.append(0)
        else:
            ngs.append(abs(s[1]))
            pss.append(0)

    ind = np.arange(0.5, i + 0.5, 1)
    ax.bar(ind, pss, 0.5, color="#4D606E")
    ax.bar(ind, ngs, 0.5, color="#3FBAC2")
    ax.set_xlim([0.0, ind[-1]+1.0])
    ax.set_xticks(ind)
    ax.set_xticklabels(labels, rotation=-45, ha="left")
    ax.legend(["Positive", "Negative"])
    ax.set_ylabel("sensitivities")
    return fig, ax


if __name__ == "__main__":
    M = Mission()
    M.cost = M["W"]
    sol = M.solve("mosek")

    varns = ["W_{pay}", "R", "S_{TO}", "h_{batt}", "(W/S)", "sp_{motor}",
             "AR", "\\eta_{prop}"]

    Fig, _ = plot_sens(M, sol, varns)
    Fig.savefig("sensbar.pdf", bbox_inches="tight")
