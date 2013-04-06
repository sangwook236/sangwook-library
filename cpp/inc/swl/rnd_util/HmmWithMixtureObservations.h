#if !defined(__SWL_RND_UTIL__HMM_WITH_MIXTURE_OBSERVATIONS__H_)
#define __SWL_RND_UTIL__HMM_WITH_MIXTURE_OBSERVATIONS__H_ 1


#include "swl/rnd_util/ExportRndUtil.h"
#include <boost/numeric/ublas/matrix.hpp>


namespace swl {

//--------------------------------------------------------------------------
// HMM with mixture observation densities

class SWL_RND_UTIL_API HmmWithMixtureObservations
{
public:
	//typedef HmmWithMixtureObservations base_type;
	typedef boost::numeric::ublas::matrix<double> dmatrix_type;

protected:
	HmmWithMixtureObservations(const size_t C, const size_t K);
	HmmWithMixtureObservations(const size_t C, const size_t K, const dmatrix_type &alphas);
public:
	virtual ~HmmWithMixtureObservations();

private:
	HmmWithMixtureObservations(const HmmWithMixtureObservations &rhs);  // not implemented
	HmmWithMixtureObservations & operator=(const HmmWithMixtureObservations &rhs);  // not implemented

public:
	//
	size_t getMixtureSize() const  {  return C_;  }

	dmatrix_type & getMixtureCoefficient()  {  return alphas_;  }
	const dmatrix_type & getMixtureCoefficient() const  {  return alphas_;  }

protected:
	void normalizeObservationDensityParameters(const size_t K);

protected:
	const size_t C_;  // the number of mixture components

	dmatrix_type alphas_;  // mixture coefficients(weights)
};

}  // namespace swl


#endif  // __SWL_RND_UTIL__HMM_WITH_MIXTURE_OBSERVATIONS__H_