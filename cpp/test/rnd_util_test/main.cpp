//#include "stdafx.h"
#if defined(_WIN32) || defined(WIN32) || defined(_WIN64) || defined(WIN64)
#include <vld/vld.h>
#endif
#include <string>
#include <vector>
#include <iostream>
#include <cstdlib>


int main(int argc, char *argv[])
{
	void tree_traversal();
	void graph_traversal();

	void levenshtein_distance();
	void dynamic_time_warping();

	void hough_transform();
	void plane3d_estimation_using_ransac();

	void rejection_sampling();
	void sampling_importance_resampling();
	void metropolis_hastings_algorithm();

	void kalman_filter();
	void extended_kalman_filter();
	void unscented_kalman_filter();
	void unscented_kalman_filter_with_additive_noise();

	void univariate_normal_mixture_model();
	void multivariate_normal_mixture_model();
	void von_mises_mixture_model();

	void hmm_with_multinomial_observation_densities();
	void hmm_with_univariate_normal_observation_densities();
	void hmm_with_univariate_normal_mixture_observation_densities();
	void hmm_with_von_mises_observation_densities();
	void hmm_with_von_mises_mixture_observation_densities();

	void ar_hmm_with_univariate_normal_observation_densities();
	void ar_hmm_with_univariate_normal_mixture_observation_densities();

	void hmm_segmentation();
	void crf_segmentation();

	int retval = EXIT_SUCCESS;
	try
	{
		// tree traversal -------------------------------------------
		tree_traversal();

		// graph traversal ------------------------------------------
		graph_traversal();

		// distance measure -----------------------------------------
		//levenshtein_distance();  // Levenshtein / edit distance.
		dynamic_time_warping();  // dynamic time warping (DTW).

		// estimation -----------------------------------------------
		//hough_transform();
		//plane3d_estimation_using_ransac();

		// sampling / resampling ------------------------------------
		//rejection_sampling();
		//sampling_importance_resampling();  // sequential importance sampling (SIS), sampling importance resampling (SIR), particle filter, bootstrap filter.
		//metropolis_hastings_algorithm();  // Markov chain Monte Carlo (MCMC).

		// Bayesian filtering ---------------------------------------
		//kalman_filter();
		//extended_kalman_filter();
		//unscented_kalman_filter();
		//unscented_kalman_filter_with_additive_noise();

		// mixture model (MM) ---------------------------------------
		//univariate_normal_mixture_model();
		//multivariate_normal_mixture_model();
		//von_mises_mixture_model();

		// hidden Markov model (HMM) --------------------------------
		//hmm_with_multinomial_observation_densities();
		//hmm_with_univariate_normal_observation_densities();
		//hmm_with_univariate_normal_mixture_observation_densities();
		//hmm_with_von_mises_observation_densities();
		//hmm_with_von_mises_mixture_observation_densities();

		// autoregressive hidden Markov model (AR HMM) --------------
		//ar_hmm_with_univariate_normal_observation_densities();
		//ar_hmm_with_univariate_normal_mixture_observation_densities();

		//-----------------------------------------------------------
		// application

		// HMM segmentation -----------------------------------------
		//hmm_segmentation();  // not yet implemented.
		//crf_segmentation();  // not yet implemented.
	}
    catch (const std::bad_alloc &e)
	{
		std::cout << "std::bad_alloc caught: " << e.what() << std::endl;
		retval = EXIT_FAILURE;
	}
	catch (const std::exception &e)
	{
		std::cout << "std::exception caught: " << e.what() << std::endl;
		retval = EXIT_FAILURE;
	}
	catch (...)
	{
		std::cout << "unknown exception caught" << std::endl;
		retval = EXIT_FAILURE;
	}

	//std::cout << "press any key to exit ..." << std::endl;
	//std::cin.get();

	return retval;
}

void output_data_to_file(std::ostream &stream, const std::string &variable_name, const std::vector<double> &data)
{
	stream << variable_name.c_str() << " = [" << std::endl;
	for (std::vector<double>::const_iterator cit = data.begin(); cit != data.end(); ++cit)
		stream << *cit << std::endl;
	stream << "];" << std::endl;
}
