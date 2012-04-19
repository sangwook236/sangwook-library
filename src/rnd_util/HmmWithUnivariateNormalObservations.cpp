#include "swl/Config.h"
#include "swl/rnd_util/HmmWithUnivariateNormalObservations.h"
#include <boost/math/distributions/normal.hpp>  // for normal distribution
#include <boost/random/normal_distribution.hpp>
#include <boost/random/variate_generator.hpp>
#include <ctime>


#if defined(_DEBUG) && defined(__SWL_CONFIG__USE_DEBUG_NEW)
#include "swl/ResourceLeakageCheck.h"
#define new DEBUG_NEW
#endif


namespace swl {

HmmWithUnivariateNormalObservations::HmmWithUnivariateNormalObservations(const size_t K)
: base_type(K, 1), mus_(K, 0.0), sigmas_(K, 0.0),  // 0-based index
  baseGenerator_()
{
}

HmmWithUnivariateNormalObservations::HmmWithUnivariateNormalObservations(const size_t K, const std::vector<double> &pi, const boost::multi_array<double, 2> &A, const std::vector<double> &mus, const std::vector<double> &sigmas)
: base_type(K, 1, pi, A), mus_(mus), sigmas_(sigmas),
  baseGenerator_()
{
}

HmmWithUnivariateNormalObservations::~HmmWithUnivariateNormalObservations()
{
}

void HmmWithUnivariateNormalObservations::doEstimateObservationDensityParametersInMStep(const size_t N, const unsigned int state, const boost::multi_array<double, 2> &observations, boost::multi_array<double, 2> &gamma, const double denominatorA)
{
	// reestimate symbol prob in each state

	size_t n;
	const double denominatorPr = denominatorA + gamma[N-1][state];

	//
	double numeratorPr = 0.0;
	for (n = 0; n < N; ++n)
		numeratorPr += gamma[n][state] * observations[n][0];
	mus_[state] = 0.001 + 0.999 * numeratorPr / denominatorPr;

	//
	numeratorPr = 0.0;
	for (n = 0; n < N; ++n)
		numeratorPr += gamma[n][state] * (observations[n][0] - mus_[state]) * (observations[n][0] - mus_[state]);
	sigmas_[state] = 0.001 + 0.999 * numeratorPr / denominatorPr;
}

void HmmWithUnivariateNormalObservations::doEstimateObservationDensityParametersInMStep(const std::vector<size_t> &Ns, const unsigned int state, const std::vector<boost::multi_array<double, 2> > &observationSequences, const std::vector<boost::multi_array<double, 2> > &gammas, const size_t R, const double denominatorA)
{
	size_t n, r;

	// reestimate symbol prob in each state
	double denominatorPr = denominatorA;
	for (r = 0; r < R; ++r)
		denominatorPr += gammas[r][Ns[r]-1][state];

	// for univariate normal distributions
	double numeratorPr = 0.0;
	for (r = 0; r < R; ++r)
		for (n = 0; n < Ns[r]; ++n)
			numeratorPr += gammas[r][n][state] * observationSequences[r][n][0];
	mus_[state] = 0.001 + 0.999 * numeratorPr / denominatorPr;

	// for univariate normal distributions
	numeratorPr = 0.0;
	for (r = 0; r < R; ++r)
		for (n = 0; n < Ns[r]; ++n)
			numeratorPr += gammas[r][n][state] * (observationSequences[r][n][0] - mus_[state]) * (observationSequences[r][n][0] - mus_[state]);
	sigmas_[state] = 0.001 + 0.999 * numeratorPr / denominatorPr;
}

double HmmWithUnivariateNormalObservations::doEvaluateEmissionProbability(const unsigned int state, const boost::multi_array<double, 2>::const_array_view<1>::type &observation) const
{
	//boost::math::normal pdf;  // (default mean = zero, and standard deviation = unity)
	boost::math::normal pdf(mus_[state], sigmas_[state]);

	return boost::math::pdf(pdf, observation[0]);
}

void HmmWithUnivariateNormalObservations::doGenerateObservationsSymbol(const unsigned int state, boost::multi_array<double, 2>::array_view<1>::type &observation, const unsigned int seed /*= (unsigned int)-1*/) const
{
	typedef boost::normal_distribution<> distribution_type;
	typedef boost::variate_generator<base_generator_type &, distribution_type> generator_type;

	if ((unsigned int)-1 != seed)
		baseGenerator_.seed(seed);

	generator_type normal_gen(baseGenerator_, distribution_type(mus_[state], sigmas_[state]));
	for (size_t d = 0; d < D_; ++d)
		observation[d] = normal_gen();
}

bool HmmWithUnivariateNormalObservations::doReadObservationDensity(std::istream &stream)
{
	if (1 != D_) return false;

	std::string dummy;
	stream >> dummy;
#if defined(__GNUC__)
	if (strcasecmp(dummy.c_str(), "univariate") != 0)
#elif defined(_MSC_VER)
	if (_stricmp(dummy.c_str(), "univariate") != 0)
#endif
		return false;

	stream >> dummy;
#if defined(__GNUC__)
	if (strcasecmp(dummy.c_str(), "normal:") != 0)
#elif defined(_MSC_VER)
	if (_stricmp(dummy.c_str(), "normal:") != 0)
#endif
		return false;

	stream >> dummy;
#if defined(__GNUC__)
	if (strcasecmp(dummy.c_str(), "mu:") != 0)
#elif defined(_MSC_VER)
	if (_stricmp(dummy.c_str(), "mu:") != 0)
#endif
		return false;

	for (size_t k = 0; k < K_; ++k)
		stream >> mus_[k];

	stream >> dummy;
#if defined(__GNUC__)
	if (strcasecmp(dummy.c_str(), "sigma:") != 0)
#elif defined(_MSC_VER)
	if (_stricmp(dummy.c_str(), "sigma:") != 0)
#endif
		return false;

	for (size_t k = 0; k < K_; ++k)
		stream >> sigmas_[k];

	return true;
}

bool HmmWithUnivariateNormalObservations::doWriteObservationDensity(std::ostream &stream) const
{
	stream << "univariate normal:" << std::endl;

	stream << "mu:" << std::endl;
	for (size_t k = 0; k < K_; ++k)
		stream << mus_[k] << ' ';
	stream << std::endl;
	
	stream << "sigma:" << std::endl;
	for (size_t k = 0; k < K_; ++k)
		stream << sigmas_[k] << ' ';
	stream << std::endl;

	return true;
}

void HmmWithUnivariateNormalObservations::doInitializeObservationDensity()
{
	// PRECONDITIONS [] >>
	//	-. std::srand() had to be called before this function is called.

	const double lb = -10000.0, ub = 10000.0;
	for (size_t k = 0; k < K_; ++k)
	{
		mus_[k] = ((double)std::rand() / RAND_MAX) * (ub - lb) + lb;
		sigmas_[k] = ((double)std::rand() / RAND_MAX) * (ub - lb) + lb;
	}
}

}  // namespace swl