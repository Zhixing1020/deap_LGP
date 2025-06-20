from typing import List

from ec.util import Parameter, ParameterDatabase

from ec import *

class GPTree (GPNodeParent):

    P_TREE: str = "tree"

    def __init__(self):
        self.child:GPNode = None
        self.owner:GPIndividual = None
    
    @classmethod
    def defaultBase(cls) -> Parameter:
        return GPDefaults.base().push(cls.P_TREE)
    
    def treeEquals(self, tree: GPTree):
        return self.child.rootedTreeEquals(tree.child)
    
    def lightClone(self) -> GPTree:
        # Like shallow copy: just replicate the GPTree object and share child
        newtree = GPTree()
        # newtree.constraints = self.constraints
        newtree.child = self.child  # NOTE: shared reference
        newtree.owner = self.owner
        # newtree.argposition = self.argposition
        # newtree.parent = self.parent
        return newtree

    def clone(self) -> GPTree:
        newtree = self.lightClone()
        if self.child is not None:
            newtree.child = self.child.clone()  # assumes GPNode.clone() exists
            newtree.child.parent = newtree
            newtree.child.argposition = 0
        # still share the same owner
        return newtree
    
    def setup(self, state:EvolutionState, base:Parameter):
        def_param = self.defaultBase()

    def __str__(self)->str:
        self.child.printRootedTreeInString()

    def buildTree(self, state:EvolutionState, thread:int):
        self.child = None