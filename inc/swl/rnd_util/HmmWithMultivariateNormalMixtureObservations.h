#if !defined(__SWL_RND_UTIL__HMM_WITH_MULTIVARIATE_NORMAL_MIXTURE_OBSERVATIONS__H_)
#define __SWL_RND_UTIL__HMM_WITH_MULTIVARIATE_NORMAL_MIXTURE_OBSERVATIONS__H_ 1


#include "swl/rnd_util/CDHMM.h"
#include "swl/rnd_util/HmmWithMixtureObservations.h"


namespace swl {

//--------------------------------------------------------------------------
// continuous density HMM with multivariate normal mixture observation densities

class SWL_RND_UTIL_API HmmWithMultivariateNormalMixtureObservations: public CDHMM, HmmWithMixtureObservations
{
public:
	typedef CDHMM base_type;
	//typedef HmmWithMixtureObservations base_type;

public:
	HmmWithMultivariateNormalMixtureObservations(const size_t K, const size_t D, const size_t C);
	HmmWithMultivariateNormalMixtureObservations(const size_t K, const size_t D, const size_t C, const std::vector<double> &pi, const boost::multi_array<double, 2> &A, const boost::multi_array<double, 2> &alphas, const boost::multi_array<double, 3> &mus, const boost::multi_array<double, 4> &sigmas);
	virtual ~HmmWithMultivariateNormalMixtureObservations();

private:
	HmmWithMultivariateNormalMixtureObservations(const HmmWithMultivariateNormalMixtureObservations &rhs);
	HmmWithMultivariateNormalMixtureObservations & operator=(const HmmWithMultivariateNormalMixtureObservations &rhs);

public:
	//
	boost::multi_array<double, 3> & getMean()  {  return mus_;  }
	const boost::multi_array<double, 3> & getMean() const  {  return mus_;  }
	boost::multi_array<double, 4>& getCovarianceMatrix()  {  return  sigmas_;  }
	const boost::multi_array<double, 4> & getCovarianceMatrix() const  {  return  sigmas_;  }

protected:
	// if state == 0, hidden state = [ 1 0 0 ... 0 0 ]
	// if state == 1, hidden state = [ 0 1 0 ... 0 0 ]
	// ...
	// if state == N-1, hidden state = [ 0 0 0 ... 0 1 ]
	/*virtual*/ double doEvaluateEmissionProbability(const unsigned int state, const boost::multi_array<double, 2>::const_array_view<1>::type &observation) const;
	// if seed != -1, the seed value is set
	/*virtual*/ void doGenerateObservationsSymbol(const unsigned int state, boost::multi_array<double, 2>::array_view<1>::type &observation, const unsigned int seed = (unsigned int)-1) const;

	// for a single independent observation sequence
	/*virtual*/ void doEstimateObservationDensityParametersInMStep(const size_t N, const boost::multi_array<double, 2> &observations, boost::multi_array<double, 2> &gamma, const double denominatorA, const size_t k);
	// for multiple independent observation sequences
	/*virtual*/ void doEstimateObservationDensityParametersInMStep(const std::vector<size_t> &Ns, const std::vector<boost::multi_array<double, 2> > &observationSequences, const std::vector<boost::multi_array<double, 2> > &gammas, const size_t R, const double denominatorA, const size_t k);

	//
	/*virtual*/ bool doReadObservationDensity(std::istream &stream);
	/*virtual*/ bool doWriteObservationDensity(std::ostream &stream) const;
	/*virtual*/ void doInitializeObservationDensity();
	/*virtual*/ void doNormalizeObservationDensityParameters()
	{
		HmmWithMixtureObservations::normalizeObservationDensityParameters(K_);
	}

private:
	boost::multi_array<double, 3> mus_;  // the sets of mean vectors of each components in the multivariate normal mixture distribution
	boost::multi_array<double, 4> sigmas_;  // the sets of covariance matrices of each components in the multivariate normal mixture distribution
};

}  // namespace swl


#endif  // __SWL_RND_UTIL__HMM_WITH_MULTIVARIATE_NORMAL_MIXTURE_OBSERVATIONS__H_
