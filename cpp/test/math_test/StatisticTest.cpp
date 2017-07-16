#include "swl/Config.h"
#include "swl/math/Statistic.h"
#include <boost/timer/timer.hpp>
#include <iostream>
#define _USE_MATH_DEFINES
#include <math.h>


#if defined(_DEBUG) && defined(__SWL_CONFIG__USE_DEBUG_NEW)
#include "swl/ResourceLeakageCheck.h"
#define new DEBUG_NEW
#endif


namespace {
namespace local {

}  // namespace local
}  // unnamed namespace

void statistic()
{
	// Basic statistics.
	{
#if 0
		std::vector<double> sample;
		sample.reserve(1000);
		for (double t = 0.0; t < 1.0; t += 0.001)
			sample.push_back(std::cos(2.0 * M_PI * 100.0 * t));
#elif 1
		const std::vector<double> sample({ 1, -3, 2, 6, 7, 13, -37, 56, -73});
#elif 0
		const std::vector<double> sample({ 0, 3, 4, 1, 2, 3, 0, 2, 1, 3, 2, 0, 2, 2, 3, 2, 5, 2, 3, 999 });
#else
		const std::vector<double> sample({
			11, 7, 14, 11, 43, 38, 61, 75, 38, 28, 12, 18, 18, 17,
			19, 32, 42, 57, 44, 114, 35, 11, 13, 10, 11, 13, 17, 13,
			51, 46, 132, 135, 88, 36, 12, 27, 19, 15, 36, 47, 65, 66,
			55, 145, 58, 12, 9, 9, 9, 11, 20, 9, 69, 76, 175, 175,
			115, 55, 14, 30, 29, 18, 48, 10, 92, 151, 90, 175, 68, 15,
			15, 7
		});
#endif

		boost::timer::auto_cpu_timer timer;
		const double &mean = swl::Statistic::mean(sample);
		std::cout << "Mean = " << mean << std::endl;

		const double &sd = swl::Statistic::standardDeviation(sample, mean);
		std::cout << "SD = " << sd << std::endl;

		const double &ssd = swl::Statistic::sampleStandardDeviation(sample, mean);
		std::cout << "Sample SD = " << ssd << std::endl;

		const double &skewness = swl::Statistic::skewness(sample, mean, sd);
		std::cout << "Skewness = " << skewness << std::endl;

		const double &kurtosis = swl::Statistic::kurtosis(sample, mean, sd);
		std::cout << "Kurtosis = " << kurtosis << std::endl;

		const double &rms = swl::Statistic::rms(sample);
		std::cout << "RMS = " << rms << std::endl;

		const double &peak = swl::Statistic::peak(sample);
		std::cout << "Peak = " << peak << std::endl;

		const double &crest = swl::Statistic::crestFactor(sample);
		std::cout << "Crest factor = " << crest << std::endl;
	}
}