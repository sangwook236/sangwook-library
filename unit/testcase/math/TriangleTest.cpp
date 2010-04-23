#include "swl/Config.h"
#include "../../UnitTestConfig.h"
#include "swl/base/String.h"
#include "swl/math/Triangle.h"


#if defined(_DEBUG) && defined(__SWL_CONFIG__USE_DEBUG_NEW)
#include "swl/ResourceLeakageCheck.h"
#define new DEBUG_NEW
#endif


namespace swl {
namespace unit_test {

//-----------------------------------------------------------------------------
//

#if defined(__SWL_UNIT_TEST__USE_BOOST_UNIT)

namespace {

struct TriangleTest
{
private:
	struct Fixture
	{
		Fixture()  // set up
		{
		}

		~Fixture()  // tear down
		{
		}
	};

public:
	void test()
	{
		Fixture fixture;

	}
};

struct TriangleTestSuite: public boost::unit_test_framework::test_suite
{
	TriangleTestSuite()
	: boost::unit_test_framework::test_suite("SWL.Math.Triangle")
	{
		boost::shared_ptr<TriangleTest> test(new TriangleTest());

		add(BOOST_CLASS_TEST_CASE(&TriangleTest::test, test), 0);

		boost::unit_test::framework::master_test_suite().add(this);
	}
} testsuite;

}  // unnamed namespace

//-----------------------------------------------------------------------------
//

#elif defined(__SWL_UNIT_TEST__USE_CPP_UNIT)

struct TriangleTest: public CppUnit::TestFixture
{
private:
	CPPUNIT_TEST_SUITE(TriangleTest);
	CPPUNIT_TEST(test);
	CPPUNIT_TEST_SUITE_END();

public:
	void setUp()  // set up
	{
	}

	void tearDown()  // tear down
	{
	}

	void test()
	{
	}
};

#endif

}  // namespace unit_test
}  // namespace swl

#if defined(__SWL_UNIT_TEST__USE_CPP_UNIT)
CPPUNIT_TEST_SUITE_REGISTRATION(swl::unit_test::TriangleTest);
//CPPUNIT_TEST_SUITE_NAMED_REGISTRATION(swl::unit_test::TriangleTest, "SWL.Math.Triangle");  // not working
#endif
