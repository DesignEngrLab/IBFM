# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:25:55 2016

@author: arlittr

Machinery for applying simple grammar rules to networkx functional models

The documentation below is more brainstorm than accurate. Expect a rewrite once 
    I nail down how it should work.

Networkx graphs are created with dummy node names, where attribute "function" 
    contains the useful function information


Write rules in source directory using spreadsheets
   all rules are stored as DSM representations of functional models (.csv)
   all rules have a left hand side (lhs) and right hand side (rhs)
       rules/rule1name/lhs.csv (left hand side)
       rules/rule1name/rhs.csv (right hand side)
    
Rule naming conventions
    Every function and flow must contain a function/flow name and a unique ID
        These UIDs will be used to fill a 'mappingUID' attribute on each node
    Terminology: Functions contain both a function and flow - a verb and object
    Function format: function-uid_flow-uid
    Flow format: flow-uid
    
    LHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword '*-UID' (e.g., Anyfunction_1) as wildcard function
        Use keyword '*-UID' (e.g., Anyflow_1) as wildcard flow
        TODO: implement functional basis hierarchy for wildcards (E.g., TransferAnyEnergy, AnySeparateAnyMaterial)
    Function blocks must contain a function and a flow, Examples:
        Protect-1_*-2
        *-1_ElectricalEnergy-2
        Protect-1_ElectricalEnergy_2
        *-1_*-2
    RHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword 'Samefunction_UID' to copy from lhs 'Anyfunction_UID' keyword
        Use keyword 'Sameflow_UID' to copy from 'Anyflow_UID' keyword
    End each new function block with a + (ProtectElectricalEnergy+)
    End each explicitly removed function block with a - (maybe? or just don't have it in the RHS?)
    End each new flow with a + (ElectricalEnergy+,MechanicalEnergy+)
        Note that muliple flows can exist in the same cell
    End each explicitly deleted flow with a - (ElectricalEnergy-,MechanicalEnergy-)

"""

import copy
import networkx as nx
import networkx.algorithms.isomorphism as iso
import ibfm_utility

class Rule(object):
    def __init__(self,name,lhspath,rhspath):
        '''
        Required arguments:
        name -- a unique name
        lhspath -- path to lhs rule, use to make a Networkx directed left hand side graph
        rhspath -- path to rhs rule, use to make a Networkx directed right hand side graph
        '''
        self.name = name
        self.lhs = self.rule2graph(lhspath)
        self.set_rhs(rhspath)
        self.anchor_nodes = set(self.lhs.nodes()).intersection(self.rhs.nodes())
        self.anchor_edges = set(self.lhs.edges()).intersection(self.rhs.edges())
        self.nodes_to_add = set(self.rhs.nodes()).difference(self.lhs.nodes())
        self.nodes_to_remove = set(self.lhs.nodes()).difference(self.rhs.nodes())
        self.edges_to_add = set(self.rhs.edges(keys=True)).difference(self.lhs.edges(keys=True))
        self.edges_to_remove = set(self.lhs.edges(keys=True)).difference(self.rhs.edges(keys=True))
        
    def set_lhs(self,path):
        self.lhs = self.rule2graph(path)
    
    def set_rhs(self,path):
        self.rhs = self.rule2graph(path)
#        for n in self.rhs.nodes():
#            self.rhs.node
#        #ensure unique keys for parallel edges on rhs
#        for n1,n2 in set(self.lhs.edges()).intersection(self.rhs.edges())      
#        
#        for n1,n2 in set(self.rhs.edges()):
#            if (n1,n2) in self.lhs.edges()
#            for a in N.edge[n1][n2].values():
#                if a['wid']
#            
#            if self.lhs[a['wid'] for a in N.edge[n1][n2].values()]
#            
#            
#            if e['wid'] in self.lhs.edges(data=True):
        #Do something to set keys according to whether new or old edge/node(?)
        
    def rule2graph(self,path):
        #Get graph
        G = ibfm_utility.ImportFunctionalModel(path,type='dsm')
        #Redo function attributes and uids
        for n,attr in G.nodes_iter(data=True):
#           verb,obj,localid,universalid = attr['function'].split('_')
            verb,obj,*attrs = attr['function'].split('_')
            
            G.node[n]['verb'] = verb
            G.node[n]['obj'] = obj
            G.node[n]['function'] = verb+'_'+obj
            if len(attrs)==1:
                G.node[n]['universalid'] = attrs[0]
            if len(attrs)==2:
                G.node[n]['universalid'] = attrs[0]
                G.node[n]['localid'] = attrs[1]
        for e1,e2,key,attr in G.edges_iter(data=True,keys=True):
            obj,*attrs = attr['flowType'].split('_')
            G.edge[e1][e2][key]['obj'] = obj
            if len(attrs)==1:
                G.edge[e1][e2][key]['universalid'] = attrs[0]
            if len(attrs)==2:
                G.edge[e1][e2][key]['universalid'] = attrs[0]
                G.edge[e1][e2][key]['localid'] = attrs[1]
        return G
        
    def recognize(self,graph,nodematchattr='function',edgematchattr='flowType'):
        '''
        Return a list of node id tuples that match the rule
        Required arguments:
        graph -- a Networkx directed graph
        matchattr -- attribute to match on
        '''
        
        wildcards = ['*','*_*']
        self.lhs.withWildcards = self.lhs
        self.lhs.withoutWildcards = copy.deepcopy(self.lhs)
        for n in self.lhs.nodes():
            if self.lhs.withoutWildcards.node[n][nodematchattr] in wildcards:
                self.lhs.withoutWildcards.remove_node(n)
        
        #Find all structural matches
        GM_structural = iso.DiGraphMatcher(graph,self.lhs)
        #Find all matches using specified functions only        
        
        #Create graph matcher between graph and lhs
        GM_content = iso.DiGraphMatcher(graph,self.lhs.withoutWildcards,
                                node_match=iso.categorical_node_match([nodematchattr],[None]),
                                edge_match=iso.categorical_edge_match([edgematchattr],[None]))
                                
        structural_mappings = [im for im in GM_structural.subgraph_isomorphisms_iter()]
        content_mappings = [im for im in GM_content.subgraph_isomorphisms_iter()]

        #List of dicts that show mappings where key = graph node and value = lhs node
        self.recognize_mappings = [sm for sm in structural_mappings 
            for cm in content_mappings if cm.items() <= sm.items()]       
        
    def apply(self,graph,location=0,nodematchattr='obj',edgematchattr='flowType'):
        '''
        Required arguments:
        graph -- a Networkx directed graph
        mapping -- a single Dict where keys are source graph node IDs and 
            values are lhs node IDs
        '''

        if len(self.recognize_mappings) > 0:
            reverse_mappings = {v: k for k, v in self.recognize_mappings[location].items()}
            this_rhs = nx.relabel_nodes(self.rhs,reverse_mappings)
            combined_graph = nx.compose(this_rhs,graph) #defaulting to attributes in graph
        else:
            raise Exception('No mappings found')
        
        print('combined:',combined_graph.nodes(data=True))
        print('to remove:',self.nodes_to_remove)
        
        #Delete nodes omitted from rhs
        for n in self.nodes_to_remove:
            
            if n in combined_graph:
                #Reconnect edges if they match flows on neighboring functions
                #This code got messy and horrible somewhere along the way...
                for p in combined_graph.predecessors(n):
                    if p not in self.rhs.nodes():
                        for s in combined_graph.successors(n):
                            for e in combined_graph.get_edge_data(p,n).values():
                                if e[edgematchattr] == combined_graph.node[s][nodematchattr]:
                                    attr = {edgematchattr:e[edgematchattr]}
                                    combined_graph.add_edge(p,s,attr_dict=attr)
                combined_graph.remove_node(n)
                
            elif n in reverse_mappings.keys():
                n = reverse_mappings[n]
                #Reconnect edges if they match flows on neighboring functions
                #This code got messy and horrible somewhere along the way...
                for p in combined_graph.predecessors(n):
                    if p not in self.rhs.nodes():
                        for s in combined_graph.successors(n):
                            for e in combined_graph.get_edge_data(p,n).values():
                                if e[edgematchattr] == combined_graph.node[s][nodematchattr] or e[edgematchattr].endswith('Signal'):
                                    attr = {edgematchattr:e[edgematchattr]}
                                    combined_graph.add_edge(p,s,attr_dict=attr)
                combined_graph.remove_node(n)
                
        return combined_graph
        
    def categorical_node_match(attr, default):
        if nx.utils.is_string_like(attr):
            def match(data1, data2):
                return data1.get(attr, default) == data2.get(attr, default)
        else:
            attrs = list(zip(attr, default)) # Python 3
    
            def match(data1, data2):
                return all(data1.get(attr, d) == data2.get(attr, d) for attr, d in attrs)
        return match  
        
class Ruleset(object):
    def __init__(self,rules={}):
        '''
        Optional arguments:
        rules -- an iterable List(?) of Rules
        '''
        self.rules = rules
    def add_rule(self,rule):
        self.rules[rule.name]['lhs'] = rule.lhs
        self.rules[rule.name]['rhs'] = rule.rhs
        
    def remove_rule(self,name):
        del self.rules[name]
        
    def get_rule(self,name):
        return self.rules[name]
        

        