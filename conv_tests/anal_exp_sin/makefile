clean-core:
	find . -name "core" -delete
clean-norms:
	find . -name "norms_raw.json" -delete
	rm -f norms_all.json
clean-resample:
	find . -path './h*/filter_resample_2d1d.py' -delete
	
clean-all: clean-norms clean-resample

pull-norms:
	test_dir=`pwd`;\
	echo $${test_dir};\
	test_case=$${test_dir##*/conv_tests/};\
	scp jan_brezina@tarkil.cesnet.cz:clanek/conv_tests/$${test_case}/norms_all.json .
	
run-all:
	RUN="1"; \
	while [  "$${RUN}" -eq "1" ]; \
	do \
		rm -f ./err; \
		echo "Starting .."; \
		pvpython ./run_all.py 2>err; \
		echo "..Ended"; \
		if [ -f err ]; then \
			if ! cat err | tail -n 3 | grep "Aborting"; \
			then \
				cat err; \
				RUN=0; \
			fi; \
		fi; \
	done; 


