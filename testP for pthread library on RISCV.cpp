#include<bits/stdc++.h>
#include<pthread.h>
#include<time.h>
#include<stdlib.h>
using namespace std;

int shared[] = {1,1,4,7};//shared memory
int sizeS = 4;//size of shared memory
int n = 4;//sizeof threads
int count1[] = {0,0,0,0};// n= 4
int lock1[2] = {0,0};
vector< vector<int> > v;
int k[] = {0,0,0,0};
int rem[] = {0,0,0,0};

int checkLock1(int id)
{
	if(lock1[id/2] != 0)
		checkLock1(id);
	else
		return 1;
}

void *sortingh(void *par)
{
	int *id =  (int *)par;
    rem[*id] = v[*id].size();
	while(rem[*id] >=4)
		{	
			sort(v[*id].begin()+k[*id] , v[*id].begin()+k[*id]+4);
			rem[*id] = rem[*id]-4;
			k[*id]+=4;
		}
	if(rem[*id] < 4)
		sort(v[*id].begin()+k[*id] , v[*id].begin()+k[*id]+rem[*id]);
		cout<<endl;
		for(int i=0;i<v[*id].size();i++)
			cout<<v[*id][i];
		cout<<endl;

	for(int i=0;i<v[*id].size();i++)
	{
		if(v[*id][i] == 1)
		count1[*id]+=1;
	}
	cout<<count1[*id]<<endl;
	
	int c = checkLock1(*id);//waititng	
	lock1[*id/2] = 1;
	for(int i=0;i<sizeS;i++)
		if(shared[i] == 1)
			count1[*id]+=1;
	lock1[*id/2] = 0;

}

int main()
{
	for(int i=0;i<n;i++)
	 	v.push_back(vector<int>());
	for(int i=0;i<n;i++)
		count1[i] = 0;
	srand(time(NULL));
	int number[n];//n=4
	for(int i=0;i<n;i++)
		number[i] = i;
	for(int i=0;i<4;i++)
		{	
			int randomNumber = rand()%3;//limit of the number of 1s in the subarray  
			for(int j=0;j<randomNumber;j++)
				v[i].push_back(0);
			int randomNumber1 = rand()%3;//limit of the number of 1s in the subarray  
			for(int j=0;j<randomNumber1;j++)
				v[i].push_back(1);
			int randomNumber2 = rand()%3;//limit of the number of 1s in the subarray  
			for(int j=0;j<randomNumber2;j++)
				v[i].push_back(3);
		}
	for(int i=0;i<4;i++)
	{
		for(int j=0;j<v[i].size();j++)
			cout<<v[i][j]<<" ";
		cout<<endl;
	}
	
	pthread_t pid[n];
	for(int i=0;i<n;i++)
	{
		pthread_create(&pid[i] , NULL ,sortingh, &number[i]);
		pthread_join(pid[i] , NULL);
	}
	for(int i=0;i<4;i++)
	{
		cout<<count1[i]<<" ";
	}

}
