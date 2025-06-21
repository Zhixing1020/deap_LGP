
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

    def setup(self, base:str):

        p = Parameter(base)

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

        if self.parameters.exists(self.P_EVALUATIONS):
            self.numEvaluations = self.parameters.getInt(self.P_EVALUATIONS, None)
            if self.numEvaluations <= 0:
                self.output.fatal("Evaluations must be >= 1 if defined.")

        if self.parameters.exists(self.P_GENERATIONS):
            self.numGenerations = self.parameters.getInt(self.P_GENERATIONS, None)
            if self.numGenerations <= 0:
                self.fatal("Generations must be >= 1 if defined.")
            if self.numEvaluations != self.__class__.UNDEFINED:
                self.output.warning("Both generations and evaluations defined. Generations will be ignored.")
                self.numGenerations = self.__class__.UNDEFINED
        elif self.numEvaluations == self.__class__.UNDEFINED:
            self.fatal("Either evaluations or generations must be defined.")

        if self.parameters.exists(self.P_NODEEVALUATIONS):
            self.numNodeEva = self.parameters.getDouble(self.P_NODEEVALUATIONS, None)
            if self.numNodeEva <= 0:
                self.fatal("Node evaluations must be >= 1 if defined.")

        # self.quitOnRunComplete = parameters.getBoolean("quit-on-run-complete", False)

        self.initializer = self.parameters.getInstanceForParameter(self.P_INITIALIZER, None, Initializer)
        self.initializer.setup(self, self.P_INITIALIZER)

        self.finisher = self.parameters.getInstanceForParameter(self.P_FINISHER, None, Finisher)
        self.finisher.setup(self, self.P_FINISHER)

        self.breeder = self.parameters.getInstanceForParameter(self.P_BREEDER, None, Breeder)
        self.breeder.setup(self, self.P_BREEDER)

        self.evaluator = self.parameters.getInstanceForParameter(self.P_EVALUATOR, None, Evaluator)
        self.evaluator.setup(self, self.P_EVALUATOR)

        self.statistics = self.parameters.getInstanceForParameterEq(self.P_STATISTICS, None, Statistics)
        self.statistics.setup(self, self.P_STATISTICS)

        self.exchanger = self.parameters.getInstanceForParameter(self.P_EXCHANGER, None, Exchanger)
        self.exchanger.setup(self, self.P_EXCHANGER)

        self.generation = 0

    def finish(self, result: int):
        self.statistics.finalStatistics(self, result)
        self.finisher.finishPopulation(self, result)
        # self.exchanger.closeContacts(self, result)
        self.evaluator.closeContacts(self, result)

    def startFresh(self):
        self.output.message("Setting up")
        self.setup(self, None)  # garbage Parameter equivalent

        # POPULATION INITIALIZATION
        self.output.message("Initializing Generation 0")
        self.statistics.preInitializationStatistics(self)
        self.population = self.initializer.initialPopulation(self, 0)
        self.statistics.postInitializationStatistics(self)

        # Compute generations from evaluations if necessary
        if self.numEvaluations > self.UNDEFINED:
            generationSize = sum(
                len(subpop.individuals) for subpop in self.population.subpops
            )

            if self.numEvaluations < generationSize:
                self.numEvaluations = generationSize
                self.numGenerations = 1
                self.output.warning(f"Using evaluations, but evaluations is less than the initial total population size ({generationSize}).  Setting to the population size.")
            else:
                if self.numEvaluations % generationSize != 0:
                    new_evals = (self.numEvaluations // generationSize) * generationSize
                    self.output.warning(f"Using evaluations, but initial total population size does not divide evenly into it.  Modifying evaluations to a smaller value ({new_evals}) which divides evenly.")
                self.numGenerations = self.numEvaluations // generationSize
                self.numEvaluations = self.numGenerations * generationSize

            self.output.message(f"Generations will be {self.numGenerations}")

        # self.exchanger.initializeContacts(self)
        self.evaluator.initializeContacts(self)

    def evolve(self):
        if self.generation > 0:
            self.output.message(f"Generation {self.generation}")

        # EVALUATION
        self.statistics.preEvaluationStatistics(self)
        self.evaluator.evaluatePopulation(self)
        self.statistics.postEvaluationStatistics(self)

        # SHOULD WE QUIT?
        if self.evaluator.runComplete(self) and self.quitOnRunComplete:
            self.output.message("Found Ideal Individual")
            return self.R_SUCCESS

        if self.generation == self.numGenerations - 1:
            return self.R_FAILURE

        # PRE-BREEDING EXCHANGING
        # self.statistics.prePreBreedingExchangeStatistics(self)
        # self.population = self.exchanger.preBreedingExchangePopulation(self)
        # self.statistics.postPreBreedingExchangeStatistics(self)

        # exchanger_msg = self.exchanger.runComplete(self)
        # if exchanger_msg is not None:
        #     self.output.message(exchanger_msg)
        #     return self.R_SUCCESS

        # BREEDING
        self.statistics.preBreedingStatistics(self)
        self.population = self.breeder.breedPopulation(self)
        self.statistics.postBreedingStatistics(self)

        # POST-BREEDING EXCHANGING
        # self.statistics.prePostBreedingExchangeStatistics(self)
        # self.population = self.exchanger.postBreedingExchangePopulation(self)
        # self.statistics.postPostBreedingExchangeStatistics(self)

        # INCREMENT GENERATION AND CHECKPOINT
        self.generation += 1
        # if self.checkpoint and self.generation % self.checkpointModulo == 0:
        #     self.output.message("Checkpointing")
        #     self.statistics.preCheckpointStatistics(self)
        #     Checkpoint.setCheckpoint(self)
        #     self.statistics.postCheckpointStatistics(self)

        return self.R_NOTDONE

    def run(self, condition: int):
        
        self.startFresh()

        result = self.R_NOTDONE
        while result == self.R_NOTDONE:
            result = self.evolve()

        self.finish(result)