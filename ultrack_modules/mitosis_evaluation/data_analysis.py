from mitosis_evaluator import evaluate_mitosis
from pandas import DataFrame, read_csv
from os import listdir
from os.path import join

data_dict = {
    "batches"  : [],
    "teste"    : [],
    "precision": [],
    "recall"   : [],
    "f1-score" : []
}

root_path = "/home/frederico-mattos/Documents/UFRGS/labsinal/projects/mitosis_evaluation/evaluate_mitosis_data"

subdir = list(map(lambda x:join(root_path, x), listdir(root_path)))

for id, dir in enumerate(sorted(subdir)):
    teste : int = id + 1
    truth_table : DataFrame = read_csv(join(dir, "mitosis_true.csv"))
    mitosis_dir : str = join(dir, "mitosis")

    for mitosis in sorted(listdir(mitosis_dir)):
        mitosis_table = read_csv(join(mitosis_dir, mitosis))
        precision, recall, f1 = evaluate_mitosis(ground_truth=truth_table,
                                                 tracking=mitosis_table,
                                                 t_tolerance=3,
                                                 p_tolerance=115)

        data_dict["batches"].append(mitosis.removeprefix("batches_").removesuffix(".csv"))
        data_dict["teste"].append(teste)
        data_dict["precision"].append(precision)
        data_dict["recall"].append(recall)
        data_dict["f1-score"].append(f1)

df = DataFrame(data_dict)

df.to_csv("analise.csv")