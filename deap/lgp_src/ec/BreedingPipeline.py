from abc import ABC, abstractmethod
from typing import List

from ec.util import Parameter

class BreedingPipeline(ABC, BreedingSource, SteadyStateBSourceForm):
    '''
     A BreedingPipeline is a BreedingSource which provides "fresh" individuals which
    can be used to fill a new population.  BreedingPipelines might include
    Crossover pipelines, various Mutation pipelines, etc.  This abstract class
    provides some default versions of various methods to simplify matters for you.
    It also contains an array of breeding sources for your convenience.  You don't
    have to use them of course, but this means you have to customize the
    default methods below to make sure they get distributed to your special
    sources.  Note that these sources may contain references to the same
    object -- they're not necessarily distinct.  This is to provide both
    some simple DAG features and also to conserve space.
    '''

    #Indicates that a source is the exact same source as the previous source.
    V_SAME = "same" 

    #Indicates the probability that the Breeding Pipeline will perform its mutative action instead of just doing reproduction.
    P_LIKELIHOOD = "likelihood"

    # Indicates that the number of sources is variable and determined by the user in the parameter file.
    DYNAMIC_SOURCES = -1

    #Standard parameter for number of sources (only used if numSources returns DYNAMIC_SOURCES
    P_NUMSOURCES = "num-sources"

    #Standard parameter for individual-selectors associated with a BreedingPipeline
    P_SOURCE = "source"

    def __init__(self):
        self.mybase = None
        self.likelihood = 1.0
        self.sources: List[BreedingSource] = []

    @abstractmethod
    def numSources(self):
        pass

    def minChildProduction(self):
        if len(self.sources) == 0:
            return 0
        return min(s.typicalIndsProduced() for s in self.sources)

    def maxChildProduction(self):
        if len(self.sources) == 0:
            return 0
        return max(s.typicalIndsProduced() for s in self.sources)

    def typicalIndsProduced(self):
        return self.minChildProduction()

    def setup(self, state:EvolutionState, base:Parameter):
        super().setup(state, base)
        self.mybase = base
        def_:Parameter = self.defaultBase()

        self.likelihood = state.parameters.getDoubleWithDefault(
            base.push(self.P_LIKELIHOOD), def_.push(self.P_LIKELIHOOD), 1.0
        )
        if self.likelihood < 0.0 or self.likelihood > 1.0:
            state.output.fatal("Breeding Pipeline likelihood must be between 0.0 and 1.0 inclusive",
                               base.push(self.P_LIKELIHOOD), def_.push(self.P_LIKELIHOOD))

        numsources:int = self.numSources()
        if numsources == self.DYNAMIC_SOURCES:
            numsources = state.parameters.getInt(base.push(self.P_NUMSOURCES), def_.push(self.P_NUMSOURCES), 0)
            if numsources == -1:
                state.output.fatal("Breeding pipeline num-sources must exist and be >= 0",
                                   base.push(self.P_NUMSOURCES), def_.push(self.P_NUMSOURCES))
        elif numsources <= self.DYNAMIC_SOURCES:
            raise RuntimeError("numSources() returned < DYNAMIC_SOURCES")
        elif state.parameters.exists(base.push(self.P_NUMSOURCES), def_.push(self.P_NUMSOURCES)):
            state.output.warning("Breeding pipeline's number of sources is hard-coded to " + str(numsources) +
                                 " yet num-sources was provided: num-sources will be ignored.",
                                 base.push(self.P_NUMSOURCES), def_.push(self.P_NUMSOURCES))

        self.sources = [None] * numsources
        for x in range(numsources):
            p = base.push(self.P_SOURCE).push(str(x))
            d = def_.push(self.P_SOURCE).push(str(x))
            s = state.parameters.getString(p, d)
            if s is not None and s == self.V_SAME:
                if x == 0:
                    state.output.fatal("Source #0 cannot be declared with \"same\".", p, d)
                self.sources[x] = self.sources[x - 1]
            else:
                self.sources[x] = state.parameters.getInstanceForParameter(p, d, BreedingSource)
                self.sources[x].setup(state, p)

        state.output.exitIfErrors()

    def clone(self):
        import copy
        c = copy.copy(self)
        c.sources = [None] * len( self.sources )
        for x in range(len(self.sources)):
            if x == 0 or self.sources[x] != self.sources[x - 1]:
                c.sources.append(self.sources[x].clone())
            else:
                c.sources.append(c.sources[x - 1])
        return c

    def reproduce(self, 
                  n:int, 
                  start:int, 
                  subpopulation:int, 
                  inds:List[Individual], 
                  state:EvolutionState, 
                  thread:int, 
                  produceChildrenFromSource:bool)->int:
        if produceChildrenFromSource:
            self.sources[0].produce(n, n, start, subpopulation, inds, state, thread)
        if isinstance(self.sources[0], SelectionMethod):
            for q in range(start, n + start):
                inds[q] = inds[q].clone()
        return n

    def produces(self, 
                 state:EvolutionState, 
                 newpop:Population, 
                 subpopulation:int, 
                 thread:int) -> boolean:
        for x in range(len(self.sources)):
            if x == 0 or self.sources[x] != self.sources[x - 1]:
                if not self.sources[x].produces(state, newpop, subpopulation, thread):
                    return False
        return True

    def prepareToProduce(self, 
                         state:EvolutionState, 
                         subpopulation:int, 
                         thread:int):
        for x in range(len(self.sources)):
            if x == 0 or self.sources[x] != self.sources[x - 1]:
                self.sources[x].prepareToProduce(state, subpopulation, thread)

    def finishProducing(self, 
                         state:EvolutionState, 
                         subpopulation:int, 
                         thread:int):
        for x in range(len(self.sources)):
            if x == 0 or self.sources[x] != self.sources[x - 1]:
                self.sources[x].finishProducing(state, subpopulation, thread)

    def preparePipeline(self, hook):
        for source in self.sources:
            source.preparePipeline(hook)

    def individualReplaced(self, 
                           state:SteadyStateEvolutionState, 
                           subpopulation:int, 
                           thread:int, 
                           individual:int):
        for source in self.sources:
            if isinstance(source, SteadyStateBSourceForm):
                source.individualReplaced(state, subpopulation, thread, individual)

    def sourcesAreProperForm(self, 
                             state:SteadyStateEvolutionState):
        for x, source in enumerate(self.sources):
            if not isinstance(source, SteadyStateBSourceForm):
                state.output.error("Source is not SteadyStateBSourceForm",
                                   self.mybase.push(self.P_SOURCE).push(str(x)),
                                   self.defaultBase().push(self.P_SOURCE).push(str(x)))
            else:
                source.sourcesAreProperForm(state)

    def defaultBase(self)->Parameter:
        # Placeholder: override as needed
        return self.mybase