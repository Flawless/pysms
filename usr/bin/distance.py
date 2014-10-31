from math import *
#import math

def distance(x1, y1, x2, y2):
    """Vincenty Inverse Solution of Geodesics on the Ellipsoid (c)
       Adapted from Chris Veness Javascript implementation:
            http://www.movable-type.co.uk/scripts/latlong-vincenty.html
                     
       Originally from: Vincenty inverse formula - T Vincenty, "Direct and Inverse Solutions of Geodesics on the 
            Ellipsoid with application of nested equations", Survey Review, vol XXII no 176, 1975   
            http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf                                             
    """
    #WGS-84 ellipsoid params
    a = 6378137.0
    b = 6356752.314245
    f = 1/298.257223563 

    L = radians(y2-y1);
    U1 = atan((1-f) * tan(radians(x1)));
    U2 = atan((1-f) * tan(radians(x2)));
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)
    cosSqAlpha = sinSigma = cosSigma = cos2SigmaM = sigma = 0.0
    lmbd = L
    lambdaP = iterLimit = 100.0

    while abs(lmbd-lambdaP) > 1e-12 and iterLimit > 0:
        iterLimit -= 1
        sinLambda = sin(lmbd)
        cosLambda = cos(lmbd);
        sinSigma = (sqrt((cosU2*sinLambda) * (cosU2*sinLambda) + 
            (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda)))

        if sinSigma==0: 
            return 0   #co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        try: #fail equatorial on python <2.6
            if isnan(cos2SigmaM):
                cos2SigmaM = 0 # equatorial line: cosSqAlpha=0 (6)
        except: 
            pass
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lambdaP = lmbd
        lmbd = (L + (1-C) * f * sinAlpha *
            (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM))))

    if iterLimit==0:
        return -1 #formula failed to converge

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
            B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    s = b*A*(sigma-deltaSigma)
    return s
