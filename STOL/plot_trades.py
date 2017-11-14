import matplotlib.pyplot    as plt
import numpy                as np
from itertools import cycle
from matplotlib.backends.backend_pdf import PdfPages
class out_data():
    def __init__(self):
        pass
    

def read_file(filename):
    fid = open(filename, 'r')
    data =  out_data()
    for line in fid:
        if ':' in line and not 'Warning' in line:
            #print '___'
            l1 = line.split(':')
            #print l1
            l =  l1[1].split()
            if not 'S_gr' in l1[0] :
                #print l
                setattr(data, l1[0], float(l[0]))


    fid.close()
    #print data
    return data

def get_filename(folder, RNWY, RNG, PAY, VCR, gLND):
    return "%s/RNWY_%4.0f_RNG_%4.0f_PAY_%4.0f_V_%3.0f_GLND_%3.0f.sum" % \
                            (folder, RNWY, RNG, PAY, VCR, gLND*10)
def plot_weight_payload_range(PAY_RANGE, RNWY, RNG, VCR, gLND):
    lines = ["k-","k--","k-.","k:"]
    linecycler = cycle(lines)

    P = len(PAY_RANGE)
    R = len(RNG)
    MTO     = np.zeros((P,R))
    PFEI    = np.zeros((P,R))
    n_pax = [p/195 for p in PAY_RANGE]

    plt.figure()
    plt.hold(True)
    for r in range(R):
        for p in range(P):

            filename    = get_filename('Analysis',RNWY, RNG[r], PAY_RANGE[p], VCR, gLND)
            out_dict    = read_file(filename)
            MTO[p,r]    = out_dict.MTO
            PFEI[p,r]   = out_dict.PFEI

        plt.plot(n_pax, MTO[:,r],next(linecycler), label = '%3.0f nmi'%RNG[r])


    plt.xlabel("Number of people onboard")
    plt.ylabel("MTOW (lbs)")
    plt.legend()
    plt.title("Runway: %3.0f ft V_CR: %3.0f kts gLND: %3.1f g"%(RNWY, VCR, gLND))
    pp = PdfPages("Runway_%3.0f_VCR_%3.0f_gLND%3.0f.pdf"%(RNWY, VCR, gLND*10))
    plt.axis([4, 20, 0, 10000])
    pp.savefig()
    pp.close()

    #plt.show()

def plot_cost_payload(PAY_RANGE, RNWY, RNG, VCR, gLND):
    lines = ["k-","k--","k-.","k:"]
    linecycler = cycle(lines)

    P = len(PAY_RANGE)
    R = len(RNWY)
    MTO     = np.zeros((P,R))
    PFEI    = np.zeros((P,R))
    cost    = np.zeros((P,R))
    cpsm    = np.zeros((P,R))
    n_pax = [p/195 for p in PAY_RANGE]

    plt.figure()
    plt.hold(True)
    for r in range(R):
        for p in range(P):

            filename    = get_filename('Analysis/Cost',RNWY[r], RNG, PAY_RANGE[p], VCR, gLND)
            out_dict    = read_file(filename)
            MTO[p,r]    = out_dict.MTO
            PFEI[p,r]   = out_dict.PFEI
            cost[p,r]   = out_dict.Trip_Cost
            cpsm[p,r]   = cost[p,r]/(n_pax[p]*RNG)
        #plt.plot(n_pax, cost[:,r],next(linecycler), label = '%3.0f ft'%RNWY[r])
        plt.plot(n_pax, cpsm[:,r],next(linecycler), label = '%3.0f ft'%RNWY[r])

    plt.xlabel("Number of people onboard")
    plt.ylabel("Cost/(seat-mile)")
    plt.legend()
    plt.title("Range: %3.0f ft V_CR: %3.0f kts gLND: %3.1f g"%(RNG, VCR, gLND))
    pp = PdfPages("CPSM_Range_%3.0f_VCR_%3.0f_gLND%3.0f.pdf"%(RNG, VCR, gLND*10))
    plt.axis([4, 20, 0, .33])
    pp.savefig()
    pp.close()

    #plt.show()
if __name__ == "__main__":
    RNWY = [250, 500]
    #RNG  = [50, 100, 150]
    RNG = 150
    PAY  = [p*195 for p in [4, 6, 8, 10, 20]]

    VCR  = 120
    gLND = .5

    #plot_weight_payload_range(PAY, RNWY, RNG, VCR, gLND)
    plot_cost_payload(PAY, RNWY, RNG, VCR, gLND)