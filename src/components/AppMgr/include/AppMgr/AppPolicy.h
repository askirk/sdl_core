/*
 * AppPolicy.h
 *
 *  Created on: Oct 5, 2012
 *      Author: vsalo
 */

#ifndef APPPOLICY_H_
#define APPPOLICY_H_

#include <string>

namespace NsAppManager
{
	
class AppPolicy
{
public:
	AppPolicy( const std::string& policy );
	~AppPolicy( );
	bool operator<(const AppPolicy& item2) const;
	const std::string& getPolicyHash() const;

private:
	const std::string mPolicy;
};

}; // namespace NsAppManager

#endif /* APPPOLICY_H_ */
