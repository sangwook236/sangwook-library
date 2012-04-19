#include "swl/Config.h"
#include "swl/rnd_util/HmmWithMixtureObservations.h"


#if defined(_DEBUG) && defined(__SWL_CONFIG__USE_DEBUG_NEW)
#include "swl/ResourceLeakageCheck.h"
#define new DEBUG_NEW
#endif


namespace swl {

HmmWithMixtureObservations::HmmWithMixtureObservations(const size_t C, const size_t K)
: C_(C), alphas_(boost::extents[K][C])  // 0-based index
//: C_(C), alphas_(boost::extents[boost::multi_array_types::extent_range(1, K+1)][boost::multi_array_types::extent_range(1, C+1)])  // 1-based index
{
}

HmmWithMixtureObservations::HmmWithMixtureObservations(const size_t C, const size_t K, const boost::multi_array<double, 2> &alphas)
: C_(C), alphas_(alphas)
{
}

HmmWithMixtureObservations::~HmmWithMixtureObservations()
{
}

void HmmWithMixtureObservations::normalizeObservationDensityParameters(const size_t K)
{
	size_t c;
	double sum;

	for (size_t k = 0; k < K; ++k)
	{
		sum = 0.0;
		for (c = 0; c < C_; ++c)
			sum += alphas_[k][c];
		for (c = 0; c < C_; ++c)
			alphas_[k][c] /= sum;
	}
}

}  // namespace swl