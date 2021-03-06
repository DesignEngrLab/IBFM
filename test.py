# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:05:16 2017

@author: hulsed
"""

from multiprocessing import *
import networkx as nx
import ibfm
import ibfmOpt
import importlib 
importlib.reload(ibfm)
importlib.reload(ibfmOpt)


if __name__ == '__main__':
    
    #t,s=ibfmOpt.policy2strs([1,2,3],3)
    #ibfmOpt.changeController()
    #importlib.reload(ibfmOpt)
    e1= ibfm.Experiment('monoprop')
    functions, fxnscores, fxnprobs, failutility, fxncost = ibfmOpt.scorefxns(e1)
    fxnreds=ibfmOpt.optRedundancy(functions, fxnscores, fxnprobs, fxncost)
    
    #graph of model: e1.model.graph
    # display: nx.draw_spectral(e1.model.graph)
    # better display? nx.draw_networkx(e1.model.graph)
    # nodes: graph.nodes()
    # edges: graph.edges()
    
    # find downstream fxn: e1.model.graph.neighbors('fxn')
    
    #actions=ibfmOpt.trackActions(e1)
    #instates=ibfmOpt.trackFlows(e1,1)
    
    #probability can now be gotten by:
    # list(e1.scenarios[51].values())[0].prob