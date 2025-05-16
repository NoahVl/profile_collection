from IPython import get_ipython
caput(beam.mono_bragg_pv, 1.03953)
pilatus2M.tiff.create_directory.set(-20)

ipython = get_ipython()
ipython.run_line_magic('run', '-i ./startup/user_collection/user_LinkamThermal.py')

sam = SampleLinkamTensile("test")
detselect(pilatus2M)

pilatus2M.cam.num_images.put(1)