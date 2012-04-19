//#include "stdafx.h"
#include "swl/Config.h"
#include "swl/rnd_util/HmmWithVonMisesObservations.h"
#include <boost/smart_ptr.hpp>
#include <sstream>
#include <fstream>
#include <iostream>
#include <ctime>
#include <stdexcept>


#if defined(_DEBUG) && defined(__SWL_CONFIG__USE_DEBUG_NEW)
#include "swl/ResourceLeakageCheck.h"
#define new DEBUG_NEW
#endif


//#define __TEST_HMM_MODEL 1
#define __TEST_HMM_MODEL 2
#define __USE_SPECIFIED_VALUE_FOR_RANDOM_SEED 1


namespace {
namespace local {

void model_reading_and_writing()
{
	// reading a model
	{
		boost::scoped_ptr<swl::CDHMM> cdhmm;

#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test1.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test2.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		const bool retval = cdhmm->readModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		// normalize pi & A
		cdhmm->normalizeModelParameters();

		cdhmm->writeModel(std::cout);
	}

	// writing a model
	{
		boost::scoped_ptr<swl::CDHMM> cdhmm;

#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		const double arrPi[] = {
			1.0/3.0, 1.0/3.0, 1.0/3.0
		};
		const double arrA[] = {
			0.9,  0.05, 0.05,
			0.45, 0.1,  0.45,
			0.45, 0.45, 0.1
		};
		const double arrMu[] = {
			0.0, 30.0, -20.0
		};
		const double arrSigma[] = {
			1.0, 2.0, 1.5
		};

		//
		std::ofstream stream("..\\data\\hmm\\von_mises_test1_writing.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		const double arrPi[] = {
			1.0/3.0, 1.0/3.0, 1.0/3.0
		};
		const double arrA[] = {
			0.5, 0.2,  0.3,
			0.2, 0.4,  0.4,
			0.1, 0.45, 0.45
		};
		const double arrMu[] = {
			0.0, -30.0, 20.0
		};
		const double arrSigma[] = {
			1.0, 2.0, 1.5
		};

		//
		std::ofstream stream("..\\data\\hmm\\von_mises_test2_writing.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		boost::const_multi_array_ref<double, 2> A(arrA, boost::extents[K][K]);
		cdhmm.reset(new swl::HmmWithVonMisesObservations(K, std::vector<double>(arrPi, arrPi + K), A, std::vector<double>(arrMu, arrMu + K), std::vector<double>(arrSigma, arrSigma + K)));

		const bool retval = cdhmm->writeModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model writing error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}
	}
}

void observation_sequence_generation(const bool outputToFile)
{
	boost::scoped_ptr<swl::CDHMM> cdhmm;

	// read a model
	{
#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test1.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test2.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		const bool retval = cdhmm->readModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		// normalize pi & A
		cdhmm->normalizeModelParameters();

		//cdhmm->writeModel(std::cout);
	}

	// generate a sample sequence
	{
#if defined(__USE_SPECIFIED_VALUE_FOR_RANDOM_SEED)
		const unsigned int seed = 34586u;
#else
		const unsigned int seed = (unsigned int)std::time(NULL);
#endif
		std::srand(seed);
		std::cout << "random seed: " << seed << std::endl;

		if (outputToFile)
		{
#if __TEST_HMM_MODEL == 1

#if 1
			const size_t N = 50;
			std::ofstream stream("..\\data\\hmm\\von_mises_test1_50.seq");
#elif 0
			const size_t N = 100;
			std::ofstream stream("..\\data\\hmm\\von_mises_test1_100.seq");
#elif 0
			const size_t N = 1500;
			std::ofstream stream("..\\data\\hmm\\von_mises_test1_1500.seq");
#endif

#elif __TEST_HMM_MODEL == 2

#if 1
			const size_t N = 50;
			std::ofstream stream("..\\data\\hmm\\von_mises_test2_50.seq");
#elif 0
			const size_t N = 100;
			std::ofstream stream("..\\data\\hmm\\von_mises_test2_100.seq");
#elif 0
			const size_t N = 1500;
			std::ofstream stream("..\\data\\hmm\\von_mises_test2_1500.seq");
#endif

#endif
			if (!stream)
			{
				std::ostringstream stream;
				stream << "file not found at " << __LINE__ << " in " << __FILE__;
				throw std::runtime_error(stream.str().c_str());
				return;
			}

			boost::multi_array<double, 2> observations(boost::extents[N][cdhmm->getObservationSize()]);
			std::vector<unsigned int> states(N, (unsigned int)-1);
			cdhmm->generateSample(N, observations, states, seed);

#if 0
			// output states
			for (size_t n = 0; n < N; ++n)
				std::cout << states[n] << ' ';
			std::cout << std::endl;
#endif

			// write a sample sequence
			swl::CDHMM::writeSequence(stream, observations);
		}
		else
		{
			const size_t N = 100;

			boost::multi_array<double, 2> observations(boost::extents[N][cdhmm->getObservationSize()]);
			std::vector<unsigned int> states(N, (unsigned int)-1);
			cdhmm->generateSample(N, observations, states, seed);

#if 0
			// output states
			for (size_t n = 0; n < N; ++n)
				std::cout << states[n] << ' ';
			std::cout << std::endl;
#endif

			// write a sample sequence
			swl::CDHMM::writeSequence(std::cout, observations);
		}
	}
}

void observation_sequence_reading_and_writing()
{
	boost::multi_array<double, 2> observations;
	size_t N = 0;  // length of observation sequence, N

#if __TEST_HMM_MODEL == 1

#if 1
	std::ifstream stream("..\\data\\hmm\\von_mises_test1_50.seq");
#elif 0
	std::ifstream stream("..\\data\\hmm\\von_mises_test1_100.seq");
#elif 0
	std::ifstream stream("..\\data\\hmm\\von_mises_test1_1500.seq");
#else
	std::istream stream = std::cin;
#endif

#elif __TEST_HMM_MODEL == 2

#if 1
	std::ifstream stream("..\\data\\hmm\\von_mises_test2_50.seq");
#elif 0
	std::ifstream stream("..\\data\\hmm\\von_mises_test2_100.seq");
#elif 0
	std::ifstream stream("..\\data\\hmm\\von_mises_test2_1500.seq");
#else
	std::istream stream = std::cin;
#endif

#endif
	if (!stream)
	{
		std::ostringstream stream;
		stream << "file not found at " << __LINE__ << " in " << __FILE__;
		throw std::runtime_error(stream.str().c_str());
		return;
	}

	// read a observation sequence
	size_t D = 0;
	const bool retval = swl::CDHMM::readSequence(stream, N, D, observations);
	if (!retval)
	{
		std::ostringstream stream;
		stream << "sample sequence reading error at " << __LINE__ << " in " << __FILE__;
		throw std::runtime_error(stream.str().c_str());
		return;
	}

	// write a observation sequence
	swl::CDHMM::writeSequence(std::cout, observations);
}

void forward_algorithm()
{
	boost::scoped_ptr<swl::CDHMM> cdhmm;

	// read a model
	{
#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test1.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test2.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		const bool retval = cdhmm->readModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		// normalize pi & A
		cdhmm->normalizeModelParameters();

		//cdhmm->writeModel(std::cout);
	}

	// read a observation sequence
	boost::multi_array<double, 2> observations;
	size_t N = 0;  // length of observation sequence, N
	{
#if __TEST_HMM_MODEL == 1

#if 1
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_50.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_100.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_1500.seq");
#else
		std::istream stream = std::cin;
#endif

#elif __TEST_HMM_MODEL == 2

#if 1
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_50.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_100.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_1500.seq");
#else
		std::istream stream = std::cin;
#endif

#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		size_t D = 0;
		const bool retval = swl::CDHMM::readSequence(stream, N, D, observations);
		if (!retval || cdhmm->getObservationSize() != D)
		{
			std::ostringstream stream;
			stream << "sample sequence reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}
	}

	const size_t K = cdhmm->getStateSize();

	// forward algorithm without scaling
	{
		boost::multi_array<double, 2> alpha(boost::extents[N][K]);
		double probability = 0.0;
		cdhmm->runForwardAlgorithm(N, observations, alpha, probability);

		//
		std::cout << "------------------------------------" << std::endl;
		std::cout << "forward algorithm without scaling" << std::endl;
		std::cout << "\tlog prob(observations | model) = " << std::scientific << std::log(probability) << std::endl;
	}

	// forward algorithm with scaling
	{
		std::vector<double> scale(N, 0.0);
		boost::multi_array<double, 2> alpha(boost::extents[N][K]);
		double logProbability = 0.0;
		cdhmm->runForwardAlgorithm(N, observations, scale, alpha, logProbability);

		//
		std::cout << "------------------------------------" << std::endl;
		std::cout << "forward algorithm with scaling" << std::endl;
		std::cout << "\tlog prob(observations | model) = " << std::scientific << logProbability << std::endl;
	}
}

void backward_algorithm()
{
	throw std::runtime_error("not yet implemented");
}

void viterbi_algorithm()
{
	boost::scoped_ptr<swl::CDHMM> cdhmm;

	// read a model
	{
#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test1.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test2.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		const bool retval = cdhmm->readModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		// normalize pi & A
		cdhmm->normalizeModelParameters();

		//cdhmm->writeModel(std::cout);
	}

	// read a observation sequence
	boost::multi_array<double, 2> observations;
	size_t N = 0;  // length of observation sequence, N
	{
#if __TEST_HMM_MODEL == 1

#if 1
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_50.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_100.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test1_1500.seq");
#else
		std::istream stream = std::cin;
#endif

#elif __TEST_HMM_MODEL == 2

#if 1
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_50.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_100.seq");
#elif 0
		std::ifstream stream("..\\data\\hmm\\von_mises_test2_1500.seq");
#else
		std::istream stream = std::cin;
#endif

#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		size_t D = 0;
		const bool retval = swl::CDHMM::readSequence(stream, N, D, observations);
		if (!retval || cdhmm->getObservationSize() != D)
		{
			std::ostringstream stream;
			stream << "sample sequence reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}
	}

	const size_t K = cdhmm->getStateSize();

	// Viterbi algorithm using direct probabilities
	{
		boost::multi_array<double, 2> delta(boost::extents[N][K]);
		boost::multi_array<unsigned int, 2> psi(boost::extents[N][K]);
		std::vector<unsigned int> states(N, (unsigned int)-1);
		double probability = 0.0;
		cdhmm->runViterbiAlgorithm(N, observations, delta, psi, states, probability, false);

		//
		std::cout << "------------------------------------" << std::endl;
		std::cout << "Viterbi algorithm using direct probabilities" << std::endl;
		std::cout << "\tViterbi MLE log prob = " << std::scientific << std::log(probability) << std::endl;
		std::cout << "\toptimal state sequence:" << std::endl;
		for (size_t n = 0; n < N; ++n)
			std::cout << states[n] << ' ';
		std::cout << std::endl;
	}

	// Viterbi algorithm using log probabilities
	{
		boost::multi_array<double, 2> delta(boost::extents[N][K]);
		boost::multi_array<unsigned int, 2> psi(boost::extents[N][K]);
		std::vector<unsigned int> states(N, (unsigned int)-1);
		double logProbability = 0.0;
		cdhmm->runViterbiAlgorithm(N, observations, delta, psi, states, logProbability, true);

		//
		std::cout << "------------------------------------" << std::endl;
		std::cout << "Viterbi algorithm using log probabilities" << std::endl;
		std::cout << "\tViterbi MLE log prob = " << std::scientific << logProbability << std::endl;
		std::cout << "\toptimal state sequence:" << std::endl;
		for (size_t n = 0; n < N; ++n)
			std::cout << states[n] << ' ';
		std::cout << std::endl;
	}
}

void mle_em_learning()
{
	boost::scoped_ptr<swl::CDHMM> cdhmm;

/*
	you can initialize the hmm model three ways:
		1) with a model, which also sets the number of states N and number of symbols M.
		2) with a random model by just specifyin N and M.
		3) with a specific random model by specifying N, M and seed.
*/

	// initialize a model
	const int initialization_mode = 1;
	if (1 == initialization_mode)
	{
#if __TEST_HMM_MODEL == 1
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test1.cdhmm");
#elif __TEST_HMM_MODEL == 2
		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		//
		std::ifstream stream("..\\data\\hmm\\von_mises_test2.cdhmm");
#endif
		if (!stream)
		{
			std::ostringstream stream;
			stream << "file not found at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		const bool retval = cdhmm->readModel(stream);
		if (!retval)
		{
			std::ostringstream stream;
			stream << "model reading error at " << __LINE__ << " in " << __FILE__;
			throw std::runtime_error(stream.str().c_str());
			return;
		}

		// normalize pi & A
		cdhmm->normalizeModelParameters();

		//cdhmm->writeModel(std::cout);
	}
	else if (2 == initialization_mode)
	{
#if defined(__USE_SPECIFIED_VALUE_FOR_RANDOM_SEED)
		const unsigned int seed = 34586u;
#else
		const unsigned int seed = (unsigned int)std::time(NULL);
#endif
		std::srand(seed);
		std::cout << "random seed: " << seed << std::endl;

		const size_t K = 3;  // the number of hidden states
		//const size_t D = 1;  // the number of observation symbols

		cdhmm.reset(new swl::HmmWithVonMisesObservations(K));

		cdhmm->initializeModel();
	}
	else
		throw std::runtime_error("incorrect initialization mode");

	// for a single observation sequence
	{
		// read a observation sequence
		boost::multi_array<double, 2> observations;
		size_t N = 0;  // length of observation sequence, N
		{
#if __TEST_HMM_MODEL == 1

#if 0
			std::ifstream stream("..\\data\\hmm\\von_mises_test1_50.seq");
#elif 0
			std::ifstream stream("..\\data\\hmm\\von_mises_test1_100.seq");
#elif 1
			std::ifstream stream("..\\data\\hmm\\von_mises_test1_1500.seq");
#else
			std::istream stream = std::cin;
#endif

#elif __TEST_HMM_MODEL == 2

#if 0
			std::ifstream stream("..\\data\\hmm\\von_mises_test2_50.seq");
#elif 0
			std::ifstream stream("..\\data\\hmm\\von_mises_test2_100.seq");
#elif 1
			std::ifstream stream("..\\data\\hmm\\von_mises_test2_1500.seq");
#else
			std::istream stream = std::cin;
#endif

#endif
			if (!stream)
			{
				std::ostringstream stream;
				stream << "file not found at " << __LINE__ << " in " << __FILE__;
				throw std::runtime_error(stream.str().c_str());
				return;
			}

			size_t D = 0;
			const bool retval = swl::CDHMM::readSequence(stream, N, D, observations);
			if (!retval || cdhmm->getObservationSize() != D)
			{
				std::ostringstream stream;
				stream << "sample sequence reading error at " << __LINE__ << " in " << __FILE__;
				throw std::runtime_error(stream.str().c_str());
				return;
			}
		}

		// Baum-Welch algorithm
		{
			const double terminationTolerance = 0.001;
			size_t numIteration = (size_t)-1;
			double initLogProbability = 0.0, finalLogProbability = 0.0;
			cdhmm->estimateParameters(N, observations, terminationTolerance, numIteration, initLogProbability, finalLogProbability);

			// normalize pi & A
			//cdhmm->normalizeModelParameters();

			//
			std::cout << "------------------------------------" << std::endl;
			std::cout << "Baum-Welch algorithm for a single observation sequence" << std::endl;
			std::cout << "\tnumber of iterations = " << numIteration << std::endl;
			std::cout << "\tlog prob(observations | initial model) = " << std::scientific << initLogProbability << std::endl;
			std::cout << "\tlog prob(observations | estimated model) = " << std::scientific << finalLogProbability << std::endl;
			std::cout << "\testimated model:" << std::endl;
			cdhmm->writeModel(std::cout);
		}
	}

	// for multiple independent observation sequences
	{
		// read a observation sequence
		std::vector<boost::multi_array<double, 2> > observationSequences;
		std::vector<size_t> Ns;  // lengths of observation sequences
		{
#if __TEST_HMM_MODEL == 1
			const size_t R = 3;  // number of observations sequences
			const std::string observationSequenceFiles[] = {
				"..\\data\\hmm\\von_mises_test1_50.seq",
				"..\\data\\hmm\\von_mises_test1_100.seq",
				"..\\data\\hmm\\von_mises_test1_1500.seq"
			};
#elif __TEST_HMM_MODEL == 2
			const size_t R = 3;  // number of observations sequences
			const std::string observationSequenceFiles[] = {
				"..\\data\\hmm\\von_mises_test2_50.seq",
				"..\\data\\hmm\\von_mises_test2_100.seq",
				"..\\data\\hmm\\von_mises_test2_1500.seq"
			};
#endif
			observationSequences.resize(R);
			Ns.resize(R);
			for (size_t r = 0; r < R; ++r)
			{
				std::ifstream stream(observationSequenceFiles[r].c_str());
				if (!stream)
				{
					std::ostringstream stream;
					stream << "file not found at " << __LINE__ << " in " << __FILE__;
					throw std::runtime_error(stream.str().c_str());
					return;
				}

				size_t D = 0;
				const bool retval = swl::CDHMM::readSequence(stream, Ns[r], D, observationSequences[r]);
				if (!retval || cdhmm->getObservationSize() != D)
				{
					std::ostringstream stream;
					stream << "sample sequence reading error at " << __LINE__ << " in " << __FILE__;
					throw std::runtime_error(stream.str().c_str());
					return;
				}
			}
		}

		const size_t R = observationSequences.size();  // number of observations sequences

		// Baum-Welch algorithm
		{
			const double terminationTolerance = 0.001;
			size_t numIteration = (size_t)-1;
			std::vector<double> initLogProbabilities(R, 0.0), finalLogProbabilities(R, 0.0);
			cdhmm->estimateParameters(Ns, observationSequences, terminationTolerance, numIteration, initLogProbabilities, finalLogProbabilities);

			// normalize pi, A, & B
			//cdhmm->normalizeModelParameters();

			//
			std::cout << "------------------------------------" << std::endl;
			std::cout << "Baum-Welch algorithm for multiple independent observation sequences" << std::endl;
			std::cout << "\tnumber of iterations = " << numIteration << std::endl;
			std::cout << "\tlog prob(observation sequences | initial model):" << std::endl;
			std::cout << "\t\t";
			for (size_t r = 0; r < R; ++r)
				std::cout << std::scientific << initLogProbabilities[r] << ' ';
			std::cout << std::endl;
			std::cout << "\tlog prob(observation sequences | estimated model):" << std::endl;
			std::cout << "\t\t";
			for (size_t r = 0; r < R; ++r)
				std::cout << std::scientific << finalLogProbabilities[r] << ' ';
			std::cout << std::endl;
			std::cout << "\testimated model:" << std::endl;
			cdhmm->writeModel(std::cout);
		}
	}
}

}  // namespace local
}  // unnamed namespace

void hmm_with_von_mises_observation_densities()
{
	//local::model_reading_and_writing();
	//const bool outputToFile = false;
	//local::observation_sequence_generation(outputToFile);
	//local::observation_sequence_reading_and_writing();

	//local::forward_algorithm();
	//local::backward_algorithm();  // not yet implemented
	//local::viterbi_algorithm();
	local::mle_em_learning();
}
