import random
import time
import copy

best_cost = 100.0

def extend_subrange(subrange, fullrange, best_config):
  is_extended = False
  if subrange == {}:
    # Initialize subrange to median values.
    for param, vals in fullrange.items():
      if type(vals) is set:
        subrange[param] = list(vals)
      else:
        median_index = (len(vals)-1)//2
        subrange[param] = [vals[median_index]]
        if len(vals) > 1:
          subrange[param].append(vals[median_index + 1])
      is_extended = True
  else:
    # Increase subrange if best config is on the corners and can be extended.
    for param in fullrange.keys():
      if type(fullrange[param]) is set:
        continue
      best_setting = best_config[param]
      is_left_subrange = subrange[param][0] == best_setting
      is_right_subrange = subrange[param][-1] == best_setting
      is_left_fullrange = fullrange[param][0] == best_setting
      is_right_fullrange = fullrange[param][-1] == best_setting
      extend_index = fullrange[param].index(best_setting)
      if is_left_subrange and not is_left_fullrange:
        subrange[param].insert(0, fullrange[param][extend_index - 1])
        is_extended = True
      elif is_right_subrange and not is_right_fullrange:
        subrange[param].append(fullrange[param][extend_index + 1])
        is_extended = True
  return is_extended

def random_search(learner, params = {}, rnn_type="", seed=0, attempts_per_param=2):
  """
  Executes a random search over the parameters, given a learner (a wrapper over a learning algorithm), and a dictionary
  mapping parameter names to their ranges (lists for ordered ranges, sets for unordered value alternatives).
  The parameters for optimization are the maximal range, random sampling considers a smaller subrange of those.
  The subrange is extended if optimal configurations lie on the boundary of the subrange.

  The learner needs to implement the following method:

  epochs_to_model_costs = learner.learn(num_epochs=num_epochs, config=config, seed=seed)

  where num_epochs is the list of epochs/checkpoints to consider for optimization, and config is a dictionary with
  a chosen (sampled) value for each hyper-parameters (number of epochs is not one of them).
  The returned epochs_to_model_costs maps epoch numbers to tuples containing (model at epoch, validation loss, lest loss).

  :param learner: Wrapper for learning algorithm.
  :param params: Maximal range to optimize for.
  :param seed: random seed.
  :return:
  """
  print("RNN type:", rnn_type)
  print("===")
  print("full parameter range:")
  print(params)
  print("===")

  shuffle_seed=0
  random.seed(shuffle_seed)
  params_subrange = {}

  best_accuracy = 0.0
  best_config = {}
  tried_configs = set()

  params_copy = params.copy()
  num_epochs = params_copy["num_epochs"]
  del params_copy["num_epochs"]

  # Two samples for each parameter to optimize (only those that have a choice)
  attempts_per_round = max(1, attempts_per_param * sum([1 for l in params_copy.values() if len(l) > 1]))

  while extend_subrange(params_subrange, params_copy, best_config):
    print("params_subrange:")
    print(params_subrange)
    print("===")

    for setting_nr in range(attempts_per_round):
      start = time.time()

      config = {}
      for param, settings in params_subrange.items():
        selection = random.choice(settings)
        config[param] = selection

      if frozenset(config.items()) not in tried_configs:
        print("\n === Running config: ===")
        print(config)
        tried_configs.add(frozenset(config.items()))
        epochs_to_model_costs = learner.learn(rnn_type=rnn_type, config=config, num_epochs=num_epochs, seed=seed)       
        shuffle_seed+=1
        random.seed(shuffle_seed)
        for num_epochs_selected, model_costs in epochs_to_model_costs.items():
          model, val_loss, val_acc = model_costs
          config["num_epochs"] = num_epochs_selected
          print(config)
          print("Val_acc: %f" % (val_acc))
          if val_acc > best_accuracy:
            best_config = copy.deepcopy(config)
            best_accuracy = val_acc
            best_model = model
        time_elapsed = time.time() - start
        print("time (s):" + str(time_elapsed))
        print("Best config and validation accuracy so far:")
        print(best_config)
        print(best_accuracy)
        print("===\n")
      else:
        print(" === already tried: ===")
        print(config)
        print("===")
  print("Best config, validation accuracy:")
  print(best_config)
  print(best_accuracy)
  print("===")
  
  return best_model, best_config

