# PADetBench

## Launch CarlaUE4

1. Commands should be executed via the "x64 Native Tools Command Prompt for VS 2022". Open this by clicking the "Windows key" and searching for "x64" and then click to open "x64 Native Tools Command Prompt for VS 2022".
2. Change to PowerShell by command `powershell`
3. Open the root CARLA folder, all commands should be run in this folder.
4. Activate the virtue environment for Carla.
5. Run `make launch GENERATOR="Visual Studio 17 2022"`

## Customize Adversarial Vehicle

1. **New vehicle blueprint**: Create a new folder for the new vehicle blueprint or directly copy others and adjust accordingly, such as folder name and vehicle blueprint name, in the proper direction, such as ".\Carla\Unreal\CarlaUE4\Content\Carla\Blueprints\Vehicles" for new vehicles.
2. **Import texture**: Go to the ***Content Browser*** tab and the corresponding folder of the adversarial vehicle. Right-click in the browser window and select `Import to ...`. Navigate to where your texture file is saved and import it.
3. **Assign adversarial texture to material**: Content Browser --> double click "Material_adv" --> click "Texture Sample" --> Select texture in the ***Details*** tab.
4. **Assign adversarial material to the vehicle**: Content Browser --> double click "BP_Audi_Etron_dta" --> click "Mesh (VehicleMesh) (Inherited)" in the ***Components*** tab --> change ***Materials***.***Element 1*** to the desired adversarial material. Then Compile and save
5. In `Content/Carla/Blueprint/Vehicle`, open the `VehicleFactory` file.
6. In the ***Generate Definitions*** tab, double-click **Vehicles**.
7. In the ***Details*** panel, expand the ***Default Value*** section and add a new element to the vehicle array.
8. Fill in the ***Make*** and ***Model*** of your vehicle.
9. Fill in the ***Class*** value with your `BP_<vehicle_name>` file.
10. Optionally, provide a set of recommended colors for the vehicle.
11. Compile and save.
