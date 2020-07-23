# Created on 2020/7/22

# This module is for importing, transforming and visualizing market data.

import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
import random as random
import matplotlib.pyplot as plt

import marketdata.simuldata as sd


def individual(number_of_genes, upper_limit, lower_limit, sum_target):
    """
    Function that creates an individual from random values that we call genes.
    These genes can represent the investment into a market or any other value in a pool of possible values.
    
    Arguments:
    - number_of_genes: it is the number of genes (but it can also be the number of assets in the market).
    - upper_limit: that's the maximum value taken by the genes (or amount we invest), before normalization.
    - lower_limit: that's the minimum value taken by the genes (or amount we invest), before normalization.
    - sum_target: that's the sum value of the genes (or the total investment that will be reached), after normalization.
    
    Note: this function has a little bug that turns out funny. If the sum of all the values is negative, then the normalization will reverse the sign,
    and we will end up having a portfolio which has flipped signes, hence specified long positions become short, and conversely. So I just put a small test.
    """
    individual = [random.random() * (upper_limit-lower_limit) + lower_limit for x in range(number_of_genes)]
    normalization = sum(individual) / sum_target
    if normalization < 0:
        raise Exception("Shorting too many assets. Not allowed for now.")
    normalized_individual = np.array(individual) / normalization
    
    return normalized_individual



def population(number_of_individuals, number_of_genes, upper_limit, lower_limit, sum_target, birth_date, name_indiv="Indiv Portfolio"):
    """
    Function that creates a population of individuals from the function `individual`.
    
    Arguments:
    number_of_individuals: the number of individuals we want in this creation of a population
    number_of_genes: the number of genes each of these individuals have
    upper_limit: the higher limit of genes, i.e. largest amount of long positions
    lower_limit: the lowest limit of genes, i.e. the lowest amount we invest in a given asset. Value can be negative (short positions).
    sum_target: the sum of all these positions.
    birth_date: a date to specify at which time the individuals of that population were created.
    name_indiv: the name we choose for the individuals.
    """
    
    # Building a data frame of individuals
    pop = pd.DataFrame([individual(number_of_genes, upper_limit, lower_limit, sum_target) for _ in range(number_of_individuals)])
    pop.columns = ["Asset " + str(i) for i in range(number_of_genes)]
    
    # Setting the birthdate
    pop["Born"] = [birth_date for _ in range(number_of_individuals)]
    
    # Setting the row names
    pop.index = [name_indiv + str(i+1) for i in range(number_of_individuals)]
    pop.index.names = ["Individuals"]
    
    return pop




def get_generation(population, market, current_eval_date, next_eval_date, lamb=0.5, fitness_method="Max Return and Vol", return_propag=False, date_format="%Y-%m"):
    """
    Takes a population, propagate its elements to the next evaluation event, and compute their fitness
    
    Arguments:
    - population: the population to evolve
    - market: the market which serves as a basis for propagation
    - current_eval_date: the present date on which we evaluate the portfolios
    - next_eval_date: the target date until which we want to make the portfolios evolve
    - return_propag: an option to return the propagations
    - date_format: format of the dates in the data frames
    
    Note: we define a generation as a population for which the fitness has been computed and who is sorted according to it.
    
    Note: - population has rows which are the names of the portfolio, and columns which are the assets.
          - propagation has rows which are the time stamps, and columns which are the names of the portfolios.
    """
    
    # Make sure all the individual portfolios were born before the current date:
    for birth_date in population['Born']:
        if birth_date >= next_eval_date:
            raise Exception("Individuals can't be born at/after the evaluation date.")
    # Make sure the next evaluation date is later than the current date:
    if current_eval_date >= next_eval_date:
        raise Exception("Current date can't be after the evaluation date.")
    
    # Getting the date just before the next evaluation date (at which reproduction will happen)
    date_before_eval = sd.find_tick_before_eval(market.index, next_eval_date)
    
    # Propagate individuals
    propagation = sd.limited_propagation(population, market, current_eval_date, date_before_eval)
    
    # Create the generation from the population copy
    try:
        generation = population.copy()
    except:
        print(population)
    
    # Remove any fitness column if it existed already (otherwise we will sum it/them after... potentially disrupting the fitness calculation)
    # This is in case we use a generation (i.e. a population with computed fitness and ranked by it) as a population argument
    # if len(generation.filter(regex='Fit').columns) != 0:
    #     generation.drop(columns=generation.filter(regex='Fit').columns.tolist(), inplace=True)
    # Not needed if we want to keep the fitness columns with dates, which sounds like a better solution for the moment
        
    # Compute the fitness of individuals and sort them by fitness
    fitness_name = "Fitness " + date_before_eval.strftime(date_format)
    generation[fitness_name] = sd.fitness_calculation(population, propagation, market, current_eval_date, next_eval_date, lamb, fitness_method)
    generation.sort_values(by=[fitness_name], ascending=False, inplace=True)
    
    if return_propag == True:
        return generation, propagation
    else:
        return generation

    
def roulette(cum_sum, chance):
    """
    The function for roulette wheel selection takes the cumulative sums and the randomly generated value
    for the selection process and returns the number of the selected individual. By calculating the cumulative sums,
    each individual has a unique value between 0 and 1. To select individuals, a number between 0 and 1 is randomly
    generated and the individual that is closes to the randomly generated number is selected.
    """
    variable = list(cum_sum.copy())
    variable.append(chance)
    variable = sorted(variable)
    return variable.index(chance)


def selection(generation, method='Fittest Half'):
    """
    Function that operates the selection among a generation, based on the last fitness.
    Different methods can be used among 'Fittest Half', 'Random' and 'Roulette Wheel'.
    
    Methods:
    'Fittest Half': the first half of the top fitness is kept
    'Random': rows are picked up at random, but they can't be the same
    'Roulette Wheel': rows are picked up at random, but with a preference for high cumulative sum (high fitness).
    """
    
    # Initialization
    N = generation.shape[0]
    
    # Sorting:
    # We use the last fitness column and normalize it
    last_fitness = generation.filter(regex='Fit').columns[-1]
    generation['Normalized Fitness'] = [generation[last_fitness][x]/sum(generation[last_fitness]) for x in range(len(generation[last_fitness]))]

    # We sort the values from smallest to highest for computing the cumulative sum
    generation.sort_values(by='Normalized Fitness', ascending=True, inplace=True)
    
    # Computing the cumulative sum
    cumsum_name = "CumSum " + last_fitness.split(" ")[1]
    generation[cumsum_name] = np.array(generation['Normalized Fitness']).cumsum()
    
    # We sort the values back, from highest fitness to lowest
    generation.sort_values(by=cumsum_name, ascending=False, inplace=True)
    
    # We get rid of the normalized fitness and just use the cumulative sum
    generation.drop(columns=["Normalized Fitness"], inplace=True)
    
    
    # Selection:
    if method == 'Fittest Half':
        select_rows = [x for x in range(N//2)]
        selected_individuals = generation.iloc[select_rows,:]
        
    elif method == 'Random':
        select_rows = [x for x in range(N)]
        random.shuffle(select_rows)
        selected_individuals = generation.iloc[select_rows[:N//2],:]
        
    elif method == 'Roulette Wheel':
        selected = []
        for x in range(N//2):
            selected.append(roulette(generation[cumsum_name], random.random()))
            while len(set(selected)) != len(selected):
                selected[x] = roulette(generation[cumsum_name], random.random())
        select_rows = [int(selected[x]) for x in range(N//2)]
        selected_individuals = generation.iloc[select_rows,:]

    return pd.DataFrame(selected_individuals)



def pairing(elite, selected, method = 'Fittest'):
    """
    Function that establishes the pairing of the selected population and elite all together.
    
    Methods:
    - 'Fittest': the top fitness individuals are paired in order, this does not check if the elite is fit however (we let evolution do that).
                 The selected individuals should be ranked from fittest to less fit if things have been done in the proper order before.
    - 'Random': the pairing is done at random, but no individual can reproduce more than once.
    - 'Weighted Random': the pairing is done with higher probability among high fitness individuals. Some individuals may reproduce several times.
    """
    
    # Combining elite and previously selected individuals
    cumsumcols_toremove = selected.filter(regex="CumSum").columns
    individuals = pd.concat([elite, selected.drop(columns=cumsumcols_toremove)])
    individuals.reindex(np.random.permutation(individuals.index))
    
    # Getting the fitness of all of them (not necessarily ordered)
    last_fitness = selected.filter(regex="Fit").columns[-1]
    Fitness = individuals[last_fitness]

    # Initialization for pairing
    M = individuals.shape[0]
    
    # odd_indiv = False
    if M%2 != 0:
        raise Exception("NUMBER OF INDIVIDUALS IS ODD ! PROBLEM WITH PAIRING !")
    
    # Start the pairing
    pairs = []
    if method == 'Fittest':
        parents_pairs = [[individuals.index[x], individuals.index[x+1]] for x in range(0,M,2)]
        parents_values = [[individuals.iloc[x], individuals.iloc[x+1]] for x in range(0,M,2)]
        
    if method == 'Random':
        pairs = [x for x in range(M)]
        random.shuffle(pairs)
        parents_pairs = []
        parents_values = []
        for x in range(0,M,2):
            parents_pairs.append([individuals.index[pairs[x]], individuals.index[pairs[x+1]]])
            parents_values.append([individuals.iloc[pairs[x]], individuals.iloc[pairs[x+1]]])
                
    if method == 'Weighted Random': # This method does not allow a parent to reproduce with himself, but allows some parent to reproduce several times!
        Normalized_Fitness = sorted([Fitness[x]/sum(Fitness) for x in range(len(Fitness))], reverse = True)
        Cumulative_Sum = np.array(Normalized_Fitness).cumsum()
        parents_pairs = []
        parents_values = []
        for x in range(M//2):
            pair = [roulette(Cumulative_Sum, random.random()), roulette(Cumulative_Sum, random.random())]
            parents_pairs.append([individuals.index[pair[0]], individuals.index[pair[1]]])
            parents_values.append([individuals.iloc[pair[0]], individuals.iloc[pair[1]]])
            while parents_pairs[x][0] == parents_pairs[x][1]:
                new_element = roulette(Cumulative_Sum, random.random())
                parents_pairs[x][1] = individuals.index[new_element]
                parents_values[x][1] = individuals.iloc[new_element]
                
    return parents_pairs, parents_values



def non_adjacent_random_list(Nmin, Nmax, Npoints):
    """
    Function that generates a list of Npoints non-adjacent numbers at random, taken from a list of integers between Nmin and Nmax.
    Extreme ends of the list Nmin, Nmin+1, ..., Nmax-1, Nmax are excluded.
    
    Note: this function is written to be used in the function `mating_pair`.
    """
    
    # Initial tests
    if Nmin%1!=0 or Nmax%1!=0 or Npoints%1!=0:
        raise Exception("Nmin, Nmax and Npoints must be integers.")

    if Npoints > int((Nmax-Nmin-2)/3):
        print("For Nmin =",Nmin,"and Nmax =",Nmax,"we must have Npoints <=",int((Nmax-Nmin-2)/5))
        raise Exception("Please take a lower value to avoid slowness.")

    # Initialization
    list_pts=[]
    count = 0

    # Process
    while count < Npoints:
        pt = random.randint(Nmin+1, Nmax-1) 
        pt_is_fine = True
        for p in list_pts:
            if np.abs(p-pt)<2:
                pt_is_fine = False
                continue
        if pt_is_fine:
            list_pts.append(pt)
            count +=1
            
    # Plot
    # fig = plt.figure(figsize=(15,5))
    # plt.hist(list_pts, bins=Nmax-Nmin)
    
    return sorted(list_pts)



def mating_pair(pair_of_parents, mating_date, method='Single Point', Npoints=None):
    """
    Function that takes a pair of parents and make a reproduction of them to produce two offsprings.
    
    Methods:
    - 'Single Point': using only one pivot value for exchange of genes
    - 'Two Points': using two pivot value for exchange of genes
    
    Note: Since the echange of genes have changed the sum of each portfolio, we are enforced to renormalize the values.
          This makes the exchange of genes harder to compare when looking at values, but it is necessary to avoi
          portfolios overall investment to change.
    """
    
    # Check that there is only 2 parents here
    if len(pair_of_parents) != 2:
        raise Exception("Only a pair of parents allowed here!")
    
    # Selecting only the columns with Asset allocations, i.e. the genes
    parents = pd.DataFrame(pair_of_parents).filter(regex="Asset")
    Ngene = parents.shape[1]
    
    # Check that the parents have the same sum
    if parents.iloc[0].sum() - parents.iloc[1].sum() > 1E-5 :
        print(parents.iloc[0].sum(), parents.iloc[1].sum())
        raise Exception("Parents must have the same sum of assets allocations.")
    parents_sum = parents.iloc[0].sum()
        
    # Creating offsprings - Method 1
    if method == 'Single Point':
        pivot_point = random.randint(1, Ngene-2)
        
        offspring1 = parents.iloc[0,0:pivot_point].append(parents.iloc[1,pivot_point:])
        if offspring1.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring1_renorm = offspring1 * parents_sum / offspring1.sum()
        offsprings = [offspring1_renorm]
        
        offspring2 = parents.iloc[1,0:pivot_point].append(parents.iloc[0,pivot_point:])
        if offspring2.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring2_renorm = offspring2 * parents_sum / offspring2.sum()
        offsprings.append(offspring2_renorm)
    
    
    # Creating offsprings - Method 2
    if method == 'Two Points':
        pivot_point_1 = random.randint(1, Ngene-1)
        pivot_point_2 = random.randint(1, Ngene)
        
        while pivot_point_2 < pivot_point_1:
            pivot_point_2 = random.randint(1, Ngene)
            
        offspring1 = parents.iloc[0,0:pivot_point_1].append(parents.iloc[1,pivot_point_1:pivot_point_2]).append(parents.iloc[0,pivot_point_2:])
        if offspring1.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring1_renorm = offspring1 * parents_sum / offspring1.sum()
        offsprings = [offspring1_renorm]
        
        offspring2 = parents.iloc[1,0:pivot_point_1].append(parents.iloc[0,pivot_point_1:pivot_point_2]).append(parents.iloc[1,pivot_point_2:])
        if offspring2.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring2_renorm = offspring2 * parents_sum / offspring2.sum()
        offsprings.append(offspring2_renorm)
    
    
    # Creating offsprings - Method 3
    if method == 'Multi Points':
        if (Npoints == None) or (Npoints == 0):
            raise Exception("Npoints must be specified.")
        if Npoints%1!=0:
            raise Exception("Npoints must be integer.")
        
        # Create a set of pivot points
        pivots = non_adjacent_random_list(0, Ngene, Npoints)
        
        # Case where Npoints is odd
        if Npoints%2==1:
            offspring1 = parents.iloc[0,0:pivots[0]]
            offspring2 = parents.iloc[1,0:pivots[0]]
            for i in range(Npoints-1):
                offspring1 = offspring1.append(parents.iloc[int((1+(-1)**i)/2), pivots[i]:pivots[i+1]])
                offspring2 = offspring2.append(parents.iloc[int((1+(-1)**(i+1))/2), pivots[i]:pivots[i+1]])
            offspring1 = offspring1.append(parents.iloc[1, pivots[Npoints-1]:Ngene])
            offspring2 = offspring2.append(parents.iloc[0, pivots[Npoints-1]:Ngene])
        
        # Case where Npoints is even
        elif Npoints%2==0:
            offspring1 = parents.iloc[0,0:pivots[0]]
            offspring2 = parents.iloc[1,0:pivots[0]]
            for i in range(Npoints-1):
                offspring1 = offspring1.append(parents.iloc[int((1+(-1)**i)/2), pivots[i]:pivots[i+1]])
                offspring2 = offspring2.append(parents.iloc[int((1+(-1)**(i+1))/2), pivots[i]:pivots[i+1]])
            offspring1 = offspring1.append(parents.iloc[0, pivots[Npoints-1]:Ngene])
            offspring2 = offspring2.append(parents.iloc[1, pivots[Npoints-1]:Ngene])
        
        # To check visually
        # print(Npoints)
        # print(pivots)
        # for d in range(parents.shape[1]):
        #     print(d, " ", parents.iloc[0,d], parents.iloc[1,d], offspring1[d], offspring2[d])
        
        
        # Renormalizations
        if offspring1.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring1_renorm = offspring1 * parents_sum / offspring1.sum()
        offsprings = [offspring1_renorm]
        if offspring2.sum() < 0:
            print("An offspring got the sum of asset allocations negative before renormalization.")
        offspring2_renorm = offspring2 * parents_sum / offspring2.sum()
        offsprings.append(offspring2_renorm)
        
    
    # Check that the sums of asset allocations are the same as before
    sum_allocations = parents.iloc[0].sum()
    if sum_allocations - parents.iloc[1].sum() > 1E-5 :
        print([parents.iloc[0], parents.iloc[1], offsprings[0], offsprings[1]])
        print(parents.iloc[0].sum(), parents.iloc[1].sum(), offsprings[0].sum(), offsprings[1].sum())
        raise Exception("Parents must all have the same sum of assets allocations.")
    if sum_allocations - offsprings[0].sum() > 1E-5 :
        print([parents.iloc[0], parents.iloc[1], offsprings[0], offsprings[1]])
        print(parents.iloc[0].sum(), parents.iloc[1].sum(), offsprings[0].sum(), offsprings[1].sum())
        raise Exception("Offsprings and parents must have the same sum of assets allocations.")
    if sum_allocations - offsprings[1].sum() > 1E-5 :
        print([parents.iloc[0], parents.iloc[1], offsprings[0], offsprings[1]])
        print(parents.iloc[0].sum(), parents.iloc[1].sum(), offsprings[0].sum(), offsprings[1].sum())
        raise Exception("Offsprings and parents must have the same sum of assets allocations.")
        
    # Adding the mating date, which is also the birth date of the offsprings (no gestation period here).
    offsprings[0]["Born"] = mating_date
    offsprings[1]["Born"] = mating_date
    
    return offsprings




































