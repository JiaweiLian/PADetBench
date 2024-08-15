# auto-detect-validation
This is a code to automatically validate a set of models as well as datasets and visualize the results. The code is designed to validate the models in the mmdetection and mmyolo tools. The code will run the validation on the provided detections and save the results in the `results.csv` file. The code will also plot the bar plot of the results and save it in the `results-bar.pdf` file. 

## Requirements
- Python 3.8
- Numpy 1.24.4
- Pandas 2.0.3
- Pytorch 2.0.0
- torchvision 0.15.0
- mmengine 0.10.4
- mmcv 2.0.0
- mmdet 3.3.0
- mmyolo 0.6.0

## Validation
To run the code, you need to provide the path to the detections and the GPU number to run the code:
```python
python validations.py --detection-path /path/to/detection --gpu 1
```

For example, if you want to validate the models in the mmdetection using 8 GPUs, you can run the following command:
```python
python validations.py --detection-path mmdetection --gpu 8
```
Then, the results will be saved in the `results/results.csv` file.

## Plotting
### Bar Plot
To plot the bar plot, you can run the following command:
```python
python plots-bar.py --data-path results/vehicle.csv --save-path results/vehicle-bar.pdf
```

### Box Plot
To plot the box plot, you can run the following command:
```python
python plots-box-victim-asr.py --data-path results/vehicle.csv --save-path results/vehicle-box.pdf
```

## Set of Models Used for Validation
The set of models used for validation are listed below in `models_list.yml` file. You can add more models or remove the existing models from the list for validation. You can check `configs` directory in both mmdetection and mmyolo to get the list of models available for validation. 