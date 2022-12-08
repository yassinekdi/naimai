output_labels = ['O', 'B-background', 'I-background', 'B-objectives', 'I-objectives',
                         'B-methods', 'I-methods', 'B-results', 'I-results']
ner_labels = ['background', 'objectives', 'methods','results', "other"]
ner_labels2 = ['BAC', 'OBJ', 'MET','RES', "OTH"]
list_colors = ['#2adddd',"#80ffb4","#ff8042","#2b7ff6","#007f00"]
colors_labels = {key: color for key,color in zip(ner_labels2,list_colors)}
threshold_tf_similarity = .05