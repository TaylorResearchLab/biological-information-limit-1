"""Plot tables and figures from calculated CSV results.

figure_data.json records the plotted rows and input file hashes.
"""
from pathlib import Path
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from _common import read_csv, write_json, digest


def record(out: Path, names: list[str], figure: str):
    write_json(out / 'figure_data.json', {'figure':figure,
        'inputs': {n:{'sha256':digest(out/n), 'rows':read_csv(out/n)} for n in names}})


def tcell(out: Path):
    name='table_1_tcell_proofreading.csv';rows=read_csv(out/name)
    n=[int(r['proofreading_steps']) for r in rows]
    info=[float(r['mutual_information_bits']) for r in rows]
    ratio=[math.log10(float(r['agonist_self_completion_ratio'])) for r in rows]
    fig,ax=plt.subplots(figsize=(7.2,4.6))
    p1,=ax.plot(n,info,marker='o',linewidth=2,label='Mutual information')
    ax.set_xlabel('Required proofreading steps');ax.set_ylabel('Information in completion outcome (bits)')
    ax.set_ylim(0,.7);ax.set_xticks(n);ax.grid(axis='y',alpha=.25)
    other=ax.twinx()
    p2,=other.plot(n,ratio,marker='s',linestyle='--',linewidth=2,label='log10 agonist/self completion ratio')
    other.set_ylabel('log10 agonist/self completion ratio');other.set_ylim(0,max(ratio)+.8)
    other.yaxis.set_major_locator(MaxNLocator(integer=True))
    for x,y in zip(n,ratio):
        other.annotate(f'$10^{{{y:g}}}$',(x,y),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
    ax.legend([p1,p2],[p1.get_label(),p2.get_label()],loc='lower left',frameon=False)
    fig.tight_layout();filename='figure_1_tcell_proofreading.png'
    fig.savefig(out/filename,dpi=350,bbox_inches='tight');plt.close(fig);record(out,[name],filename)


def ribosome(out: Path):
    names=['table_2_ribosome_information.csv','table_3_ribosome_passage.csv']
    local=read_csv(out/names[0]);passage=read_csv(out/names[1])
    fig,ax=plt.subplots(figsize=(8.6,4.8));ax.set_axis_off();ax.set_xlim(0,1);ax.set_ylim(0,1)
    box=dict(boxstyle='round,pad=0.42',fill=False,linewidth=1.4)
    for x,label in zip([.09,.36,.63,.90],['Original tRNA\nencounter','Initial selection','Proofreading','Accepted peptide\nproduct']):
        ax.text(x,.80,label,ha='center',va='center',bbox=box,fontsize=10.5)
    for x0,x1 in [(.17,.28),(.44,.55),(.71,.82)]:
        ax.annotate('',xy=(x1,.80),xytext=(x0,.80),arrowprops=dict(arrowstyle='->',linewidth=1.4))
    ax.text(.32,.52,'Upstream passage $a_s$\nsets how many and which tRNAs\nreach proofreading',ha='center',va='center',fontsize=8.8)
    labels={'wild_type':'WT','restrictive':'Restrictive'}
    bounds='\n'.join(f"{labels[r['ribosome_preparation']]}: {float(r['information_min_bits']):.3f}–{float(r['information_max_bits']):.3f} bits" for r in local)
    ax.text(.62,.52,'Proofreading acceptance\nconstrains local information\n'+bounds,ha='center',va='center',fontsize=8.5)
    ax.text(.89,.52,'Final peptide-product ratio\nalso depends on upstream\nfactor $U$',ha='center',va='center',fontsize=8.5)
    ax.axhline(.34,linewidth=.8)
    ep=' → '.join(f"{float(r['passage_probability_both_classes']):g}" for r in passage)
    bits=' → '.join(f"{float(r['terminal_information_bits']):.3g}" for r in passage)
    ax.text(.50,.23,f'With proofreading fixed, passage {ep}\nInformation per original encounter {bits} bits',ha='center',va='center',fontsize=9.2)
    ax.text(.50,.07,'Local proofreading information and whole-encounter information are different quantities.',ha='center',va='center',fontsize=9.3)
    fig.tight_layout();filename='figure_2_ribosome_selection.png'
    fig.savefig(out/filename,dpi=350,bbox_inches='tight');plt.close(fig);record(out,names,filename)


def msn2(out: Path):
    names=['table_4_msn2_information.csv','table_5_msn2_pairing.csv']
    panel=read_csv(out/names[0]);reveals=read_csv(out/names[1])
    labels=['1-copy: 100 nM vs 3 μM','1-copy: 175 nM vs 7 pulses','2-copy: 7 vs 8 pulses','',
            '175 nM vs 7 pulses: neither paired','  sustained condition paired','  7-pulse condition paired','  both conditions paired']
    data=panel+[None]+reveals;observed=[float(r['observed_paired_information_bits']) for r in panel]
    observed=observed+[None]+[observed[1]]*len(reveals)
    fig,ax=plt.subplots(figsize=(7.4,5.5));ys=list(range(len(labels)))[::-1]
    for y,r,o in zip(ys,data,observed):
        if r is not None:
            ax.plot([float(r['information_min_bits']),float(r['information_max_bits'])],[y,y],linewidth=5,solid_capstyle='butt')
            ax.plot(o,y,marker='o',markersize=6)
    ax.set_yticks(ys);ax.set_yticklabels(labels,fontsize=9);ax.set_xlim(0,1)
    ax.set_xlabel('Mutual information (bits)');ax.grid(axis='x',alpha=.25)
    ax.set_title('Information compatible with incomplete versus paired Msn2 reporter observations',fontsize=11)
    ax.text(0,ys[4]+.65,'Progressive restoration of same-cell pairing',fontsize=9.5,fontweight='bold')
    fig.tight_layout();filename='figure_3_msn2_information.png'
    fig.savefig(out/filename,dpi=350,bbox_inches='tight');plt.close(fig);record(out,names,filename)
