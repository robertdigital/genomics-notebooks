# -*- coding: utf-8 -*-
'''
.. module:: popgen
   :synopsis: Viewing results
   :noindex:
   :copyright: Copyright 2014 by Tiago Antao
   :license: GNU Affero, see LICENSE for details

.. moduleauthor:: Tiago Antao <tra@popgen.net>

'''

from collections import defaultdict
import statistics

import matplotlib.pyplot as plt


class View():
    def __init__(self, model, stats=[], max_y=None):
        self.model = model
        self.stats = stats
        self.max_y = max_y
        model.register(self)

    def start(self):
        pass

    def end(self):
        pass

    def set_sim_id(self, sim_id):
        self._sim_id = sim_id

    def set_pop(self, pop):
        self.pop = pop

    def complete_sim(self):
        pass

    def complete_cycle(self, pop):
        pass

    @property
    def view_ops(self):
        view_ops = []
        for param in self.params:
            param.set_pop(self.pop)
            view_ops.extend(param.simupop_stats)
        return view_ops


class BasicView(View):
    def __init__(self, model, params, stats=[], max_y=None, with_model=False):
        View.__init__(self, model, stats, max_y)
        self.with_model = with_model
        self.params = params
        info_fields = []
        for param in params:
            info_fields.extend(param.simupop_info)
        self.info_fields = list(set(info_fields))

    def start(self):
        self.results = {}
        self.stat_results = {}
        self._num_sims = len(self.model._sim_ids)
        for stat in self.stats:
            self.stat_results[stat] = {}
        for param in self.params:
            self.results[param.name] = [[] for x in range(self._num_sims)]
            for stat in self.stats:
                self.stat_results[stat][param.name] = [[] for x in
                                                       range(self._num_sims)]

    def complete_cycle(self, pop):
        for param in self.params:
            param.sample_size = self.model._sim_ids[self._sim_id]['sample_size']
            vals = param.get_values(pop)
            if len(self.results[param.name][self._sim_id]) == 0:
                for i in range(len(vals)):
                    self.results[param.name][self._sim_id].append([vals[i]])
            else:
                for i in range(len(vals)):
                    self.results[param.name][self._sim_id][i].append(vals[i])
            for stat in self.stats:
                if stat == 'mean':
                    fun = statistics.mean
                stat_dict = self.stat_results[stat][param.name][self._sim_id]
                stat_dict.append(fun(vals))

    def end(self):
        try:
            vparam = list(self.model._variation_params.keys())[0]
        except IndexError:
            # Single parameter, lets show pop_size
            vparam = 'pop_size'
        fig, axs = plt.subplots(len(self.params) +
                                (1 if self.with_model else 0),
                                self._num_sims,
                                figsize=(16, 9), squeeze=False)
        if self.with_model:
            for i, param in enumerate(self.model._sim_ids):
                ax = axs[0, i]
                self.model._draw_sim(ax, param)
                cval = str(param[vparam])
                ax.set_title('%s: %s' % (vparam, cval))
                if i != 0:
                    plt.setp(ax.get_yticklabels(), visible=False)
                    plt.setp(ax.get_xticklabels(), visible=False)
        for i, param in enumerate(self.params):
            min_param = None
            max_param = None
            for sim_id, results in enumerate(self.results[param.name]):
                if self.with_model:
                    ax = axs[i + 1, sim_id]
                else:
                    ax = axs[i, sim_id]
                    if i == 0:
                        cval = str(self.model._sim_ids[sim_id][vparam])
                        ax.set_title('%s: %s' % (vparam, cval))
                plt.setp(ax.get_xticklabels(), visible=False)
                if sim_id != 0:
                    plt.setp(ax.get_yticklabels(), visible=False)
                for my_case in results:
                    ax.plot(my_case)
                for stat in self.stats:
                    stat_dict = self.stat_results[stat][param.name]
                    ax.plot(stat_dict[sim_id], 'k', lw=4)
                ymin, ymax = ax.get_ylim()
                if min_param is None or ymin < min_param:
                    min_param = ymin
                if max_param is None or ymax > max_param:
                    max_param = ymax
            for sim_id, results in enumerate(self.results[param.name]):
                if self.with_model:
                    ax = axs[i + 1, sim_id]
                else:
                    ax = axs[i, sim_id]
                ax.set_ylim(min_param, max_param)
        if not self.with_model:
            plt.setp(axs[len(self.params) - 1, 0].get_xticklabels(),
                     visible=True)
        fig.tight_layout()
        return fig


class BasicViewTwo(View):
    def __init__(self, model, param, stats=[], highlight=None):
        View.__init__(self, model, stats)
        info_fields = []
        info_fields.extend(param.simupop_info)
        self.info_fields = list(set(info_fields))
        self.params = [param]
        self.param = param
        self.highlight = highlight

    def start(self):
        self.results = {}
        self._num_sims = len(self.model._sim_ids)
        self.results[self.param] = [[] for x in range(self._num_sims)]
        vparams = list(self.model._variation_params.keys())
        vparams.sort()

    def complete_cycle(self, pop):
        self.param.sample_size = self.model._sim_ids[self._sim_id]['sample_size']
        vals = self.param.get_values(pop)
        if len(self.results[self.param][self._sim_id]) == 0:
            for i in range(len(vals)):
                self.results[self.param][self._sim_id].append([vals[i]])
        else:
            for i in range(len(vals)):
                self.results[self.param][self._sim_id][i].append(vals[i])

    def end(self):
        def get_sim_id(p1, v1, p2, v2):
            for i, sim_params in enumerate(self.model._sim_ids):
                if sim_params[p1] == v1 and sim_params[p2] == v2:
                    return i
        vparams = list(self.model._variation_params.keys())
        vparams.sort()
        p1 = self.model._variation_params[vparams[0]]
        p2 = self.model._variation_params[vparams[1]]
        fig, axs = plt.subplots(len(p2), len(p1),
                                sharex=True, sharey=True,
                                figsize=(16, 9), squeeze=False)
        for i in range(len(p1)):
            v1 = p1[i]
            for j in range(len(p2)):
                v2 = p2[j]
                ax = axs[j, i]
                plt.setp(ax.get_yticklabels(), visible=False)
                plt.setp(ax.get_xticklabels(), visible=False)
                sim_id = get_sim_id(vparams[0], v1, vparams[1], v2)
                if j == 0:
                    cval = str(self.model._sim_ids[sim_id][vparams[0]])
                    axs[j, i].set_title('%s: %s' % (vparams[0], cval))
                results = self.results[self.param][sim_id]
                for l, my_case in enumerate(results):
                    if self.highlight is None or l in self.highlight:
                        axs[j, i].plot(my_case)
                    else:
                        axs[j, i].plot(my_case, 'k', lw=0.5)
        plt.setp(axs[0, 0].get_yticklabels(), visible=True)
        plt.setp(axs[0, len(p1) - 1].get_xticklabels(), visible=True)
        fig.tight_layout()
        for j in range(len(p2)):
            ax = axs[j, len(p1) - 1]
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.text(xmax + 1, ymax, '%s: %s' % (vparams[1], p2[j]),
                    ha='left', va='top', rotation='vertical')
        return fig


class MetaVsDemeView(View):
    def __init__(self, model, meta_param, deme_param, stats=[], max_y=None):
        View.__init__(self, model, stats, max_y)
        self.meta_param = meta_param
        self.deme_param = deme_param
        self.params = [meta_param, deme_param]
        info_fields = []
        info_fields.extend(meta_param.simupop_info)
        info_fields.extend(deme_param.simupop_info)
        self.info_fields = list(set(info_fields))

    def start(self):
        # need to add stats
        self._num_sims = len(self.model._sim_ids)
        self.deme_results = [defaultdict(list) for x in range(self._num_sims)]
        self.meta_results = [[] for x in range(self._num_sims)]

    def complete_cycle(self, pop):
        # need to add stats
        self.deme_param.sample_size = self.model._sim_ids[self._sim_id]['sample_size']
        self.meta_param.sample_size = self.model._sim_ids[self._sim_id]['sample_size']
        for sub_pop in range(pop.numSubPop()):
            vals = self.deme_param.get_values(pop, sub_pop)
            if len(self.deme_results[self._sim_id][sub_pop]) == 0:
                for i in range(len(vals)):
                    self.deme_results[self._sim_id][sub_pop].append([vals[i]])
            else:
                for i in range(len(vals)):
                    self.deme_results[self._sim_id][sub_pop][i].append(vals[i])

        vals = self.meta_param.get_values(pop)
        if len(self.meta_results[self._sim_id]) == 0:
            for i in range(len(vals)):
                self.meta_results[self._sim_id].append([vals[i]])
        else:
            for i in range(len(vals)):
                self.meta_results[self._sim_id][i].append(vals[i])

    def end(self):
        max_sub_pops = max([len(self.deme_results[i]) for i in
                            range(len(self.deme_results))])
        fig, axs = plt.subplots(self._num_sims, 1 + max_sub_pops,
                                sharex=True, sharey=True,
                                squeeze=False, figsize=(16, 9))
        y_min = float('inf')
        y_max = float('-inf')
        for i, param in enumerate(range(self._num_sims)):
            n_sub_pops = len(self.deme_results[i])
            ax = axs[i, 0]
            ax.set_axis_bgcolor('0.9')
            plt.setp(ax.get_yticklabels(), visible=False)
            plt.setp(ax.get_xticklabels(), visible=False)
            for my_case in self.meta_results[i]:
                ax.plot(my_case)
                if y_min > min(my_case):
                    y_min = min(my_case)
                if max(my_case) != float('inf') and y_max < max(my_case):
                    y_max = max(my_case)
            ax.set_xlim(0, len(my_case))
            for sp in range(n_sub_pops):
                ax = axs[i, sp + 1]
                plt.setp(ax.get_yticklabels(), visible=False)
                plt.setp(ax.get_xticklabels(), visible=False)
                for my_case in self.deme_results[i][sp]:
                    ax.plot(my_case)
                    if y_min > min(my_case):
                        y_min = min(my_case)
                    if max(my_case) != float('inf') and y_max < max(my_case):
                        y_max = max(my_case)

        ax = axs[self._num_sims - 1, 0]
        plt.setp(ax.get_yticklabels(), visible=True)
        plt.setp(ax.get_xticklabels(), visible=True)
        if self.max_y is None:
            ax.set_ylim(y_min, y_max)
        else:
            ax.set_ylim(y_min, self.max_y)
        fig.subplots_adjust(hspace=0, wspace=0)

        return fig


class IndividualView():
    # XXX merge with view
    def __init__(self, model, param, step=10, with_model=False):
        self.model = model
        model.register(self)
        info_fields = []
        info_fields.extend(param.simupop_info)
        self.info_fields = list(set(info_fields))
        self.param = param
        self.params = [param]
        self.gen = 0
        self.step = step
        self.with_model = with_model

    def set_sim_id(self, sim_id):
        self._sim_id = sim_id

    def set_pop(self, pop):
        self.pop = pop

    def complete_sim(self):
        self.gen = 0

    @property
    def view_ops(self):
        view_ops = []
        for param in self.params:
            param.set_pop(self.pop)
            view_ops.extend(param.simupop_stats)
        return view_ops

    def start(self):
        self.gen = 0
        self.results = {}
        self._num_sims = len(self.model._sim_ids)
        self.results = [[] for x in range(self._num_sims)]

    def complete_cycle(self, pop):
        if self.gen % self.step != 0:
            self.gen += 1
            return
        self.param.sample_size = self.model._sim_ids[
            self._sim_id]['sample_size']
        vals = self.param.get_values(pop)
        self.results[self._sim_id].append(vals)
        self.gen += 1

    def end(self):
        try:
            vparam = list(self.model._variation_params.keys())[0]
        except IndexError:
            # Single parameter, lets show pop_size
            vparam = 'pop_size'
        all_steps = max([len(x) for x in self.results])
        fig, axs = plt.subplots(all_steps +
                                (1 if self.with_model else 0),
                                self._num_sims,
                                figsize=(16, 4 * all_steps), squeeze=False)
        if self.with_model:
            for i, param in enumerate(self.model._sim_ids):
                ax = axs[0, i]
                self.model._draw_sim(ax, param)
                cval = str(param[vparam])
                ax.set_title('%s: %s' % (vparam, cval))
                if i != 0:
                    plt.setp(ax.get_yticklabels(), visible=False)
                    plt.setp(ax.get_xticklabels(), visible=False)
        for i, param in enumerate(range(all_steps)):
            for sim_id, results in enumerate(self.results):
                if self.with_model:
                    ax = axs[i + 1, sim_id]
                else:
                    ax = axs[i, sim_id]
                    if i == 0:
                        cval = str(self.model._sim_ids[sim_id][vparam])
                        ax.set_title('%s: %s' % (vparam, cval))
            for sim_id, results in enumerate(self.results):
                sp_pos = defaultdict(list)
                for (sp, ind), (x, y) in results[i].items():
                    sp_pos[sp].append((x, y))
                if self.with_model:
                    ax = axs[i + 1, sim_id]
                else:
                    ax = axs[i, sim_id]
                for c, (sp, vals) in enumerate(sp_pos.items()):
                    x, y = zip(*vals)
                    try:
                        dot = ['.', '<', '>', 'v', '^', '8', 's', 'p',
                               '*'][c // 7]
                    except IndexError:
                        dot = ','
                    ax.plot(x, y, dot)
        if not self.with_model:
            plt.setp(axs[all_steps - 1, 0].get_xticklabels(),
                     visible=True)
        fig.tight_layout()
        return fig
