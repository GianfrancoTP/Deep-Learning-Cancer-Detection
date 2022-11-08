# dataset_generator.py

Este archivo tiene como propósito generar de manera completamente **automática** la base de datos a partir de los archivos *.svs* y *.xml* que entregó el Dr. Araya. El programa genera los datos, dando como resultado, múltiples parches generados de una sola imagen.

---

# Como se usa?

## Input

Para generar los parches a partir de los archivos .svs, es necesario guardar la carpeta del caso con sus imágenes .svs en “**./data/input**” con sus respectivos archivos .xml. Por ejemplo, si queremos generar los parches a partir de todas las imágenes del caso “*i0-249-2022”*, entonces tendremos que guardar las imágenes en “**./data/input/i0-249-2022**”.  

El programa también cuenta con múltiples inputs distintos para configurar las distintas opciones de los parches que se generan:

```python
input_path = './data/input'

tile_size = 100
# Minimum percentage of positive pixels in tile to be considered as positive.
min_positive_percentage = 0.8 
# Maximum percentage of positive pixels in tile to be considered as negative.
max_positive_percentage = 0.1
# Minimum percentage of tissue pixels to be considered a useful tile.
tissue_percentage = 0.85
# Minimum tiled pixel brightness to be considered as background.
gray_scale_cut = 215
```

- ***input_path***: **Dirección** de la carpeta donde se guardan los archivos .svs y .xml que se desea procesar. El programa leerá automáticamente todas las carpetas dentro del directorio y generará todos los parches a partir de cada uno de los casos.
- ***tile_size***: Esta variable nos permite elegir el **tamaño** en píxeles de los parches. Por ejemplo, si nuestra variable vale “100”, entonces los parches generados serán cuadrados de dimensiones 100x100 píxeles.
- ***min_positive_percentage***: Porcentaje **mínimo** de píxeles con cáncer para que un parche sea etiquetado como parche **positivo**. Es decir, si elegimos el valor “0.8”, entonces solo los parches que tengan un 80% o más de contenido con cáncer serán etiquetados como positivos.
- ***max_positive_percentage***: Porcentaje **máximo** de píxeles con cáncer que debe tener un parche, para que sea considerado negativo. Es decir, si elegimos el valor “0.1”, entonces solo los parches que tengan 10% o menos de contenido con cáncer serán etiquetados como negativos.
- ***tissue_percentage***: Porcentaje mínimo de pixeles con tejido que debe contener un parche para que esté dentro de la base de datos. De lo contrario, el parche será descartado y no será guardado.
- ***gray_scale_cut***: Esta variable indica el valor mínimo que debe tener un píxel (en escala de grises) para que sea considerado como parte de fondo y **NO** como un tejido. Es decir, si se usa el valor “*225*”, entonces estamos diciendo que todos los píxeles que tengan un brillo promedio entre los tres canales RGB de *225* o más, serán considerados como fondo.
    
    Por ejemplo, si tenemos el píxel con los valores *220*, *255*, *230* en sus respectivos canales RGB, este será considerado como parte del fondo, ya que el promedio de los tres canales (*235*) es mayor a *225*.
    
    $( 220 + 255 + 230)/3 = 235$ 
    
    Aquí podemos ver unos ejemplos de distintos ***gray_scale_cut*** que van desde 210 al 230. Se puede notar que cuando usamos un valor de 230, este no distingue bien el tejido del fondo, por lo que es necesario bajarlo a 220 o 215 para distinguir bien entre ambos elementos.
    
    ![Screenshot_1.png](/imagenes/Screenshot_1.png)
    

## Output

El resultado del programa es guardado en una carpeta con el nombre “**dataset (NxN)**” dentro del directorio “**./data**” donde N es el tamaño en píxeles de los parches. Por ejemplo, si generamos una base de datos con parches de tamaño 250px, entonces la carpeta de salida donde se guardaran todos los parches será “**./data/dataset (250x250)**”.

Las imágenes serán guardadas en carpetas con el nombre de su caso respectivo en formato *.jpeg*. Además, cada caso tendrá subcarpetas con el nombre de las imágenes donde contendrán los parches respectivos de cada archivo .*svs* del caso. Por último, cada caso tendrá además dos carpetas con los nombres “***negative”*** y “***positive”*** donde vendrán todos los parches generados con su etiqueta correspondiente. O sea, todos los parches con la etiqueta “negativo” estarán en la carpeta “***negative”*** y los parches con la etiqueta “positivo” estarán en la carpeta “***positive”.***

## Ejemplos de usos

Si queremos simplemente correr el programa con los valores *defaults* entonces usamos el siguiente comando en consola:

```powershell
> python dataset_generator.py 
```

También, si queremos cambiar alguna variable, como el ***tile_size*** (tamaño de los parches) a 200x200 pixeles, entonces usamos el parámetro “-s”. Un ejemplo de esto se puede ver a continuación usando los comandos de consola.

```powershell
> python dataset_generator.py -s 200
```

Igualmente, si queremos cambiar las variables ***min_positive_percentage*** por 85% y el ***gray_scale_cut*** de 220, usamos los parámetros “-min” y “-b” respectivamente como se observa a continuación:

```powershell
> python dataset_generator.py -min 0.85 -b 220
```

A continuación, podemos observar una tabla con todos los parámetros modificables para la creación de la base de datos.

| Argumentos | Descripción  | Valor default |
| --- | --- | --- |
| -h | Show this help message and exit | None |
| -i | Input file path | ”./data/input” |
| -o | Output file path | “./data/dataset (NxN)” |
| -s | Size of tiles | 100 |
| -min | Minimum percentage of positive pixels in tile to be considered as positive | 0.8 |
| -max | Maximum percentage of positive pixels in tile to be considered as negative | 0.1 |
| -t | Minimum percentage of tissue pixels to be considered a useful tile | 0.85 |
| -b | Minimum tiled pixel brightness to be considered as background | 215 |