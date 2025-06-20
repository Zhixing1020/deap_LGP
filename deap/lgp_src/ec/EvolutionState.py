
from ec.util import *

import random

class EvolutionState:

    # Run status codes
    R_SUCCESS: int = 0
    R_FAILURE: int = 1
    R_NOTDONE: int = 2

    UNDEFINED: int = -1

    # Parameter keys
    P_INITIALIZER: str = "init"
    P_FINISHER: str = "finish"
    P_BREEDER: str = "breed"
    P_EVALUATOR: str = "eval"
    P_STATISTICS: str = "stat"
    P_EXCHANGER: str = "exch"
    P_GENERATIONS: str = "generations"
    P_NODEEVALUATIONS: str = "nodeevaluations"
    P_EVALUATIONS: str = "evaluations"

    def __init__(self, parameterPath:str):
        # ParameterDatabase
        self.parameters = ParameterDatabase(parameterPath)

        self.output = Output()

        self.random : [random] = [random] * 1

        self.breedthreads:int = 0
        self.evalthreads:int = 1

        self.generation = self.__class__.UNDEFINED
        self.numGeneration = 200
        
        self.nodeEvaluation = self.__class__.UNDEFINED
        self.numNodeEva = 1e7

        self.population = None  # will be a Population instance
        self.evaluator = None  # Evaluator instance
        self.initializer = None  # Initializer instance
        self.breeder = None  # Breeder instance
        self.statistics = None  # Statistics instance

    def setup(self, parameters):
        self.parameters = parameters

        # self.data = [{} for _ in self.random]  # per-thread data

        # self.checkpoint = parameters.getBoolean("checkpoint", False)
        # self.checkpointPrefix = parameters.getString("checkpoint-prefix")

        # if self.checkpointPrefix is None:
        #     old_prefix = parameters.getString("prefix")
        #     if old_prefix is None:
        #         self.fatal("No checkpoint prefix specified.")
        #     else:
        #         self.output.warning("The parameter 'prefix' is deprecated. Please use 'checkpoint-prefix'.")
        #         self.checkpointPrefix = old_prefix
        # elif parameters.getString("prefix") is not None:
        #     self.output.warning("You have BOTH 'prefix' and 'checkpoint-prefix' defined. Using 'checkpoint-prefix'.")

        # self.checkpointModulo = parameters.getInt("checkpoint-modulo", 1)
        # if self.checkpointModulo <= 0:
        #     self.fatal("The checkpoint modulo must be an integer > 0.")

        # if parameters.exists("checkpoint-directory"):
        #     self.checkpointDirectory = parameters.getFile("checkpoint-directory")
        #     if self.checkpointDirectory is None:
        #         self.fatal("The checkpoint directory name is invalid.")
        #     if not self.checkpointDirectory.is_dir():
        #         self.fatal("The checkpoint directory is not a directory.")

        if parameters.exists(self.P_EVALUATIONS):
            self.numEvaluations = parameters.getInt(self.P_EVALUATIONS, None)
            if self.numEvaluations <= 0:
                self.output.fatal("Evaluations must be >= 1 if defined.")

        if parameters.exists(self.P_GENERATIONS):
            self.numGenerations = parameters.getInt(self.P_GENERATIONS, None)
            if self.numGenerations <= 0:
                self.fatal("Generations must be >= 1 if defined.")
            if self.numEvaluations != self.__class__.UNDEFINED:
                self.output.warning("Both generations and evaluations defined. Generations will be ignored.")
                self.numGenerations = self.__class__.UNDEFINED
        elif self.numEvaluations == self.__class__.UNDEFINED:
            self.fatal("Either evaluations or generations must be defined.")

        if parameters.exists(self.P_NODEEVALUATIONS):
            self.numNodeEva = parameters.getDouble(self.P_NODEEVALUATIONS, None)
            if self.numNodeEva <= 0:
                self.fatal("Node evaluations must be >= 1 if defined.")

        # self.quitOnRunComplete = parameters.getBoolean("quit-on-run-complete", False)

        self.initializer = parameters.getInstanceForParameter(self.P_INITIALIZER, None, Initializer)
        self.initializer.setup(self, self.P_INITIALIZER)

        self.finisher = parameters.getInstanceForParameter(self.P_FINISHER, None, Finisher)
        self.finisher.setup(self, self.P_FINISHER)

        self.breeder = parameters.getInstanceForParameter(self.P_BREEDER, None, Breeder)
        self.breeder.setup(self, self.P_BREEDER)

        self.evaluator = parameters.getInstanceForParameter(self.P_EVALUATOR, None, Evaluator)
        self.evaluator.setup(self, self.P_EVALUATOR)

        self.statistics = parameters.getInstanceForParameterEq(self.P_STATISTICS, None, Statistics)
        self.statistics.setup(self, self.P_STATISTICS)

        self.exchanger = parameters.getInstanceForParameter(self.P_EXCHANGER, None, Exchanger)
        self.exchanger.setup(self, self.P_EXCHANGER)

        self.generation = 0

    def finish(self, result: int):
        pass

    def startFresh(self):
        pass

    def evolve(self) -> int:
        return self.R_NOTDONE

    def run(self, condition: int):
        
        self.startFresh()

        result = self.R_NOTDONE
        while result == self.R_NOTDONE:
            result = self.evolve()

        self.finish(result)