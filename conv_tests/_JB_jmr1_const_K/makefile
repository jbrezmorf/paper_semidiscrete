clean-norms:
	find . -name "norms_raw.json" -delete
	rm -f norms_all.json
clean-resample:
	find . -path './h*/filter_resample_2d1d.py' -delete
	
clean-all: clean-norms clean-resample
	
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


