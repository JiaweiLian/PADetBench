# Customize Adversarial Vehicle

1. **New vehicle blueprint**: Create a new folder for the new vehicle blueprint or directly copy others and adjust accordingly, such as folder name and vehicle blueprint name, in the proper direction, such as ".\Carla\Unreal\CarlaUE4\Content\Carla\Blueprints\Vehicles" for new vehicles. 
![](../images/new_blueprint.jpg)

2. **Import texture**: Go to the ***Content Browser*** tab and the corresponding folder of the adversarial vehicle created in step 1. Right-click in the browser window and select `Import to ...`. Navigate to where your texture file (perturbation image) is saved and import it. 
![](../images/import_texture_image.jpg)

3. **Assign adversarial texture to material**: Content Browser --> double click "Material_random" --> click "Texture Sample" --> Select texture in the ***Details*** tab, which is uploaded in step 2. 
![](../images/material_adv.jpg)
![](../images/apply_texture.jpg)

4. **Assign adversarial material to the vehicle**: Content Browser --> double click blueprint, such as "BP_Audi_Etron_random" (named by yourself) --> click "Mesh (VehicleMesh) (Inherited)" in the ***Components*** tab --> change ***Materials***.***Element 1*** to the desired adversarial material. Then Compile and save.
![](../images/customize_blueprint.jpg)
![](../images/apply_material.jpg)

5. In `Content/Carla/Blueprint/Vehicle`, open the `VehicleFactory` file.
![](../images/vehicle_factory.jpg)

6. In the ***Generate Definitions*** tab, click **Vehicles**.
![](../images/vehicles.jpg)

7. In the ***Details*** panel, expand the ***Default Value*** section and add a new element to the vehicle array.
![](../images/add_vehicle.jpg)

8. Fill in the ***Make*** and ***Model*** of your vehicle.
9. Fill in the ***Class*** value with your `BP_<vehicle_name>` file.
![](../images/enter_vehicle_information.jpg)

10. Optionally, provide a set of recommended colors for the vehicle.
11. Compile and save.
![](../images/compile&save.jpg)

12. Other adversarial actors can be customized similarly.